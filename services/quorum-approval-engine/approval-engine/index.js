const { getTierConfig, SENSITIVITY_TIERS } = require('../src/config/sensitivity');
const AnonymityService = require('../src/services/anonymityService');

/**
 * M-of-N Quorum Approval Engine
 * Core logic handlers for sensitivity thresholds, self-approval hard blocks, and anonymous pooling.
 */
class QuorumApprovalEngine {
  constructor(db, auditService) {
    this.db = db;
    this.auditService = auditService;
  }

  /**
   * Generates formatted error object with status code and error code
   */
  _createError(message, statusCode, code) {
    const error = new Error(message);
    error.statusCode = statusCode;
    error.code = code;
    return error;
  }

  /**
   * Calculates next version (e.g. 1.0 -> 1.1)
   */
  bumpVersion(currentVersion) {
    const parts = (currentVersion || '1.0').split('.');
    const major = parts[0] || '1';
    const minor = parseInt(parts[1] || '0', 10) + 1;
    return `${major}.${minor}`;
  }

  /**
   * Resolves M-of-N threshold bounds based on sensitivity tier (LOW: 1-of-1, MEDIUM: 2-of-3, HIGH: 3-of-5)
   */
  getSensitivityThresholds(tier) {
    return getTierConfig(tier);
  }

  /**
   * Validates self-approval constraints:
   * 1. Requester cannot be added to approval pool (requesterId != approverId)
   * 2. Requester cannot cast a vote on their own request (requesterId != voterId)
   */
  assertNoSelfApproval(requesterId, approverOrPool) {
    if (Array.isArray(approverOrPool)) {
      if (approverOrPool.includes(requesterId)) {
        throw this._createError(
          `Self-approval violation: Requester ID '${requesterId}' cannot be included in the approval pool.`,
          400,
          'REQUESTER_IN_APPROVAL_POOL'
        );
      }
    } else if (requesterId === approverOrPool) {
      throw this._createError(
        `403 Forbidden: Requester '${approverOrPool}' is strictly prohibited from voting on their own edit request.`,
        403,
        'SELF_APPROVAL_FORBIDDEN'
      );
    }
  }

  /**
   * Generates pseudonymous identifiers (Approver_XXXX) for pool approvers
   */
  createAnonymousPoolMap(requestId, poolMemberIds) {
    const map = {};
    poolMemberIds.forEach((approverId) => {
      map[approverId] = AnonymityService.generatePseudonym(requestId, approverId);
    });
    return map;
  }

  /**
   * Evaluates current vote state against M threshold for approval or rejection
   */
  evaluateQuorum(thresholdM, poolSizeN, votes, poolMembers) {
    const approveVotes = votes.filter((v) => v.vote_choice === 'APPROVE');
    const rejectVotes = votes.filter((v) => v.vote_choice === 'REJECT');

    if (approveVotes.length >= thresholdM) {
      return { status: 'APPROVED', isFinal: true, approveVotes, rejectVotes };
    }
    if (poolMembers.length - rejectVotes.length < thresholdM) {
      return { status: 'REJECTED', isFinal: true, approveVotes, rejectVotes };
    }
    return { status: 'PENDING', isFinal: false, approveVotes, rejectVotes };
  }
}

module.exports = {
  QuorumApprovalEngine,
  SENSITIVITY_TIERS,
  getTierConfig,
  AnonymityService
};
