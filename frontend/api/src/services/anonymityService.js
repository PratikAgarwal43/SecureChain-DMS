const crypto = require('crypto');

/**
 * Anonymity Service to handle pseudonymous identifiers and payload sanitization
 */
class AnonymityService {
  /**
   * Generates a deterministic, non-reversible pseudonymous token for an approver in a specific request context.
   * Format: Approver_<HASH_4_CHARS>
   */
  static generatePseudonym(requestId, approverId) {
    const hash = crypto
      .createHash('sha256')
      .update(`${requestId}:${approverId}:securechain_salt_sih26190`)
      .digest('hex')
      .substring(0, 4)
      .toUpperCase();
    return `Approver_${hash}`;
  }

  /**
   * Sanitizes an edit request object for external or approver consumption.
   * Masks real approver IDs and only returns anonymous pseudonyms and stats.
   */
  static sanitizeForPublic(editRequest, poolMembers = [], votes = []) {
    const anonymousPool = poolMembers.map((member) => ({
      pseudonym: member.pseudonym
    }));

    const anonymousVotes = votes.map((vote) => ({
      pseudonym: vote.voter_pseudonym,
      vote_choice: vote.vote_choice,
      created_at: vote.created_at
    }));

    return {
      id: editRequest.id,
      document_id: editRequest.document_id,
      requester_id: editRequest.requester_id,
      proposed_content: editRequest.proposed_content,
      sensitivity_tier: editRequest.sensitivity_tier,
      threshold_m: editRequest.threshold_m,
      pool_size_n: editRequest.pool_size_n,
      status: editRequest.status,
      created_at: editRequest.created_at,
      approval_pool: anonymousPool,
      votes: anonymousVotes,
      vote_counts: {
        approve: votes.filter((v) => v.vote_choice === 'APPROVE').length,
        reject: votes.filter((v) => v.vote_choice === 'REJECT').length,
        total_votes: votes.length
      }
    };
  }
}

module.exports = AnonymityService;
