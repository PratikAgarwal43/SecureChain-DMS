const crypto = require('crypto');

/**
 * WORM Audit Service
 * Enforces immutable, append-only security audit logs for all approval events.
 */
class AuditService {
  constructor(db) {
    this.db = db;
  }

  /**
   * Logs a critical approval lifecycle event to the WORM audit log.
   */
  async logEvent(eventType, requestId, documentId, requesterId, actionDetails) {
    const auditEntry = {
      id: `audit_${crypto.randomBytes(8).toString('hex')}`,
      event_type: eventType,
      request_id: requestId,
      document_id: documentId,
      requester_id: requesterId,
      action_details: actionDetails,
      timestamp: new Date().toISOString()
    };

    await this.db.insertWormAuditLog(auditEntry);
    return auditEntry;
  }

  /**
   * Fetches audit log records for verification & compliance checks.
   */
  async getAuditLogs(requestId = null) {
    return this.db.getWormAuditLogs(requestId);
  }
}

module.exports = AuditService;
