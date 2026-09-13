const crypto = require('crypto');
const AnonymityService = require('./anonymityService');
const CryptoService = require('./cryptoService');
const { getRankLevel, isSeniorLeadership } = require('../config/hierarchy');

/**
 * Escalation & Emergency Override Service
 * Handles 24-Hour SLA Backup Routing and 48-Hour Emergency Overrides with 7-Day Post-Hoc Audits.
 * SecureChain DMS (SIH26190)
 */
class EscalationService {
  static SLA_24_HOURS_MS = 24 * 60 * 60 * 1000;
  static EMERGENCY_48_HOURS_MS = 48 * 60 * 60 * 1000;
  static POST_HOC_AUDIT_DAYS = 7;

  constructor(db, auditService) {
    this.db = db;
    this.auditService = auditService;
  }

  _createError(message, statusCode, code) {
    const error = new Error(message);
    error.statusCode = statusCode;
    error.code = code;
    return error;
  }

  /**
   * Evaluates pending approvers on an edit request and escalates any overdue approvers (> 24 hours)
   * to their pre-mapped backup approvers.
   */
  async process24HourEscalation(requestId, options = {}) {
    const editReq = await this.db.getEditRequest(requestId);
    if (!editReq) {
      throw this._createError(`Edit request '${requestId}' not found`, 404, 'REQUEST_NOT_FOUND');
    }

    if (editReq.status !== 'PENDING') {
      return { escalated: false, message: `Request is already in '${editReq.status}' status.` };
    }

    const poolMembers = await this.db.getPoolMembers(requestId);
    const votes = await this.db.getVotes(requestId);
    const votedOfficerIds = new Set(votes.map((v) => v.voter_user_id));

    const now = options.currentTime ? new Date(options.currentTime).getTime() : Date.now();
    const simulatedHours = options.simulatedHoursElapsed !== undefined ? options.simulatedHoursElapsed : null;

    const escalatedMembers = [];

    for (const member of poolMembers) {
      // If member hasn't voted yet
      if (!votedOfficerIds.has(member.approver_user_id)) {
        const assignedTime = new Date(member.assigned_at || editReq.created_at).getTime();
        const elapsedMs = now - assignedTime;
        const isOverdue = simulatedHours !== null ? simulatedHours >= 24 : elapsedMs >= EscalationService.SLA_24_HOURS_MS;

        if (isOverdue || options.forceEscalate) {
          // Look up officer to find pre-mapped backup
          const officer = await this.db.getOfficer(member.approver_user_id);
          const backupOfficerId = officer ? officer.backup_approver_id : null;

          if (!backupOfficerId) {
            continue; // No pre-mapped backup available
          }

          // Generate new pseudonym for backup approver
          const newPseudonym = AnonymityService.generatePseudonym(requestId, backupOfficerId);

          // Update pool member record in database
          await this.db.escalatePoolMember(requestId, member.approver_user_id, backupOfficerId, newPseudonym);

          // Log WORM Audit Trail for 24-Hour SLA Breach & Backup Handover
          await this.auditService.logEvent('APPROVER_ESCALATED_24H', requestId, editReq.document_id, editReq.requester_id, {
            original_approver_pseudonym: member.pseudonym,
            backup_approver_pseudonym: newPseudonym,
            escalation_reason: '24-hour response SLA exceeded without vote',
            timestamp: new Date().toISOString()
          });

          escalatedMembers.push({
            originalApproverId: member.approver_user_id,
            originalPseudonym: member.pseudonym,
            backupApproverId: backupOfficerId,
            backupPseudonym: newPseudonym
          });
        }
      }
    }

    return {
      escalated: escalatedMembers.length > 0,
      escalatedCount: escalatedMembers.length,
      escalations: escalatedMembers
    };
  }

  /**
   * Executes 48-Hour Emergency Override by high-ranking leadership (e.g. Magistrate, SSP, DIG).
   * Flags request as CRITICAL severity, opens a 7-day post-hoc audit window, creates a hash-chained version,
   * and unmasks identities for judicial accountability.
   */
  async execute48HourEmergencyOverride(requestId, authorityOfficerId, reason, options = {}) {
    const editReq = await this.db.getEditRequest(requestId);
    if (!editReq) {
      throw this._createError(`Edit request '${requestId}' not found`, 404, 'REQUEST_NOT_FOUND');
    }

    if (editReq.status !== 'PENDING') {
      throw this._createError(`Cannot override request in '${editReq.status}' status.`, 400, 'REQUEST_CLOSED');
    }

    // 1. Verify Authority Rank: Must be senior leadership (SSP, Magistrate, DIG, etc.)
    const authorityOfficer = await this.db.getOfficer(authorityOfficerId);
    if (!authorityOfficer || !isSeniorLeadership(authorityOfficer.rank)) {
      throw this._createError(
        `Emergency override requires Senior Leadership authority (SSP, Magistrate, DIG). Officer '${authorityOfficerId}' is not authorized.`,
        403,
        'UNAUTHORIZED_EMERGENCY_AUTHORITY'
      );
    }

    // 2. Verify 48-Hour Inactivity Window
    const reqCreatedAt = new Date(editReq.created_at).getTime();
    const now = options.currentTime ? new Date(options.currentTime).getTime() : Date.now();
    const elapsedMs = now - reqCreatedAt;
    const isOverdue = options.simulatedHoursElapsed !== undefined
      ? options.simulatedHoursElapsed >= 48
      : elapsedMs >= EscalationService.EMERGENCY_48_HOURS_MS;

    if (!isOverdue && !options.forceOverride) {
      const remainingHours = ((EscalationService.EMERGENCY_48_HOURS_MS - elapsedMs) / (1000 * 60 * 60)).toFixed(1);
      throw this._createError(
        `48-Hour Emergency Override cannot be executed yet. Request is only ${((elapsedMs) / (1000 * 60 * 60)).toFixed(1)} hours old. ${remainingHours} hours remaining until override window opens.`,
        400,
        'EMERGENCY_OVERRIDE_TIMELOCK_ACTIVE'
      );
    }

    // 3. Calculate 7-Day Post-Hoc Audit Window Deadline
    const overrideTimestamp = new Date(now).toISOString();
    const auditDeadline = new Date(now + EscalationService.POST_HOC_DAYS_MS || now + 7 * 24 * 60 * 60 * 1000).toISOString();

    // 4. Update Request Status to APPROVED with CRITICAL severity and audit window
    const updatedReq = await this.db.setEmergencyOverrideStatus(requestId, {
      status: 'APPROVED',
      sensitivity_tier: 'CRITICAL',
      is_emergency_override: true,
      emergency_override_by: authorityOfficerId,
      emergency_override_reason: reason || '48-hour quorum timeout emergency intervention',
      emergency_override_at: overrideTimestamp,
      identity_revealed_at: overrideTimestamp,
      audit_window_deadline: auditDeadline,
      audit_status: 'MANDATORY_7DAY_POST_HOC_AUDIT_PENDING'
    });

    // 5. Bump Document Version with Cryptographic Hash Chaining
    const doc = await this.db.getDocument(editReq.document_id);
    const parts = (doc.current_version || '1.0').split('.');
    const nextVersionNum = `${parts[0] || '1'}.${parseInt(parts[1] || '0', 10) + 1}`;

    // Get previous version to link hash chain
    const versions = await this.db.getDocumentVersions(doc.id);
    const lastVersion = versions[versions.length - 1];
    const previousVersionHash = lastVersion
      ? lastVersion.current_version_hash
      : CryptoService.GENESIS_HASH;

    const contentHash = CryptoService.hashContent(editReq.proposed_content);
    const currentVersionHash = CryptoService.computeVersionHash({
      previousVersionHash,
      versionNumber: nextVersionNum,
      contentHash,
      approvedByRequestId: requestId,
      timestamp: overrideTimestamp
    });

    const authorityDscSig = CryptoService.generateDscSignature(
      authorityOfficerId,
      requestId,
      'EMERGENCY_APPROVE',
      overrideTimestamp
    );

    const versionCreated = await this.db.createDocumentVersion({
      id: `ver_${crypto.randomBytes(8).toString('hex')}`,
      document_id: doc.id,
      version_number: nextVersionNum,
      content: editReq.proposed_content,
      approved_by_request_id: requestId,
      previous_version_hash: previousVersionHash,
      current_version_hash: currentVersionHash,
      dsc_signatures: [{
        signatory_id: authorityOfficerId,
        role: authorityOfficer.rank,
        signature: authorityDscSig,
        signed_at: overrideTimestamp
      }],
      created_at: overrideTimestamp
    });

    await this.db.updateDocumentVersion(doc.id, nextVersionNum, editReq.proposed_content);

    // 6. Log WORM Audit Entry
    await this.auditService.logEvent('EMERGENCY_OVERRIDE_EXECUTED', requestId, doc.id, editReq.requester_id, {
      severity: 'CRITICAL',
      authority_officer_id: authorityOfficerId,
      authority_rank: authorityOfficer.rank,
      reason: reason || '48-hour quorum timeout emergency intervention',
      post_hoc_audit_deadline: auditDeadline,
      audit_status: 'MANDATORY_7DAY_POST_HOC_AUDIT_PENDING',
      version_created: nextVersionNum,
      version_hash: currentVersionHash
    });

    const poolMembers = await this.db.getPoolMembers(requestId);
    const votes = await this.db.getVotes(requestId);

    return {
      success: true,
      message: '48-Hour Emergency Override executed successfully. Request promoted to APPROVED with CRITICAL severity.',
      request: AnonymityService.sanitizeForPublic(updatedReq, poolMembers, votes),
      new_version: versionCreated,
      audit_window: {
        opened_at: overrideTimestamp,
        deadline: auditDeadline,
        status: 'MANDATORY_7DAY_POST_HOC_AUDIT_PENDING',
        duration_days: 7
      }
    };
  }
}

module.exports = EscalationService;
