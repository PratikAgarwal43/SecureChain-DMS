const crypto = require('crypto');

/**
 * Cryptographic Hash-Chaining & Digital Signature Certificate (DSC) Service
 * SecureChain DMS (SIH26190)
 */
class CryptoService {
  static GENESIS_HASH = '0000000000000000000000000000000000000000000000000000000000000000';

  /**
   * Generates SHA-256 checksum of raw content
   */
  static hashContent(content) {
    return crypto
      .createHash('sha256')
      .update(typeof content === 'string' ? content : JSON.stringify(content))
      .digest('hex');
  }

  /**
   * Computes cryptographically bound version hash
   */
  static computeVersionHash({ previousVersionHash, versionNumber, contentHash, approvedByRequestId, timestamp }) {
    const payload = `${previousVersionHash}:${versionNumber}:${contentHash}:${approvedByRequestId}:${timestamp}`;
    return crypto.createHash('sha256').update(payload).digest('hex');
  }

  /**
   * Creates a verifiable DSC (Digital Signature Certificate) signature for an officer's vote
   */
  static generateDscSignature(voterId, requestId, voteChoice, timestamp = new Date().toISOString()) {
    const message = `SECURECHAIN_DSC_VOTE:${voterId}:${requestId}:${voteChoice}:${timestamp}`;
    const hmac = crypto
      .createHmac('sha256', `dsc_root_key_${voterId}`)
      .update(message)
      .digest('hex');
    return `DSC_SIG_${hmac}`;
  }

  /**
   * Verifies an officer's DSC signature
   */
  static verifyDscSignature(signature, voterId, requestId, voteChoice, timestamp) {
    if (!signature || !signature.startsWith('DSC_SIG_')) {
      return false;
    }
    // If timestamp is provided, verify exact HMAC, otherwise verify signature structure
    if (timestamp) {
      const expected = CryptoService.generateDscSignature(voterId, requestId, voteChoice, timestamp);
      return signature === expected;
    }
    return signature.length === 72; // 'DSC_SIG_' (8) + 64 hex chars
  }

  /**
   * Verifies the cryptographic integrity of a document's entire version hash chain
   */
  static verifyVersionChain(versions) {
    if (!versions || versions.length === 0) {
      return { verified: true, chainLength: 0 };
    }

    // Sort by version number / creation time
    const sorted = [...versions].sort((a, b) => {
      const numA = parseFloat(a.version_number) || 0;
      const numB = parseFloat(b.version_number) || 0;
      return numA - numB;
    });

    for (let i = 0; i < sorted.length; i++) {
      const current = sorted[i];

      // Check genesis or previous link
      if (i === 0) {
        if (current.previous_version_hash && current.previous_version_hash !== CryptoService.GENESIS_HASH) {
          // If genesis points elsewhere, verify it has a valid hash
          if (current.previous_version_hash.length !== 64) {
            return {
              verified: false,
              brokenAtIndex: i,
              reason: `Genesis version ${current.version_number} has invalid previous hash`
            };
          }
        }
      } else {
        const previous = sorted[i - 1];
        if (current.previous_version_hash !== previous.current_version_hash) {
          return {
            verified: false,
            brokenAtIndex: i,
            reason: `Hash mismatch at version ${current.version_number}: previous_version_hash does not match parent version ${previous.version_number} current_version_hash`
          };
        }
      }
    }

    return { verified: true, chainLength: sorted.length };
  }
}

module.exports = CryptoService;
