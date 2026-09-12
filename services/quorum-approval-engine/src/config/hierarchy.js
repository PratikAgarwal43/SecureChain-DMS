/**
 * Police & Judicial Rank Hierarchy & Jurisdictional Pool Filtering
 * SecureChain DMS (SIH26190)
 */

const RANKS = {
  CONSTABLE: { title: 'Constable', level: 1 },
  HEAD_CONSTABLE: { title: 'Head Constable', level: 2 },
  ASI: { title: 'Assistant Sub-Inspector', level: 3 },
  SI: { title: 'Sub-Inspector', level: 4 },
  SHO: { title: 'Station House Officer / Inspector', level: 5 },
  DSP: { title: 'Deputy Superintendent of Police / ACP', level: 6 },
  SP: { title: 'Superintendent of Police', level: 7 },
  SSP: { title: 'Senior Superintendent of Police', level: 8 },
  FSL_HEAD: { title: 'Forensic Science Lab Director / Head', level: 9 },
  MAGISTRATE: { title: 'Judicial / District Magistrate', level: 9 },
  DIG: { title: 'Deputy Inspector General of Police', level: 10 },
  COMMISSIONER: { title: 'Commissioner of Police', level: 11 }
};

const STATE_WIDE_JURISDICTIONS = ['STATE_LEVEL', 'JUDICIAL_CIRCUIT', 'APEX_FSL', 'HEADQUARTERS'];

function normalizeRank(rank) {
  if (!rank) return 'SI';
  const key = String(rank).toUpperCase().trim();
  if (RANKS[key]) return key;
  // Handle variations e.g. "INSPECTOR" or "SHO"
  if (key === 'INSPECTOR') return 'SHO';
  if (key === 'ACP') return 'DSP';
  return key;
}

function getRankLevel(rank) {
  const norm = normalizeRank(rank);
  const entry = RANKS[norm];
  if (!entry) {
    throw new Error(`Unknown officer rank: '${rank}'`);
  }
  return entry.level;
}

function isEqualOrHigherRank(approverRank, requesterRank) {
  return getRankLevel(approverRank) >= getRankLevel(requesterRank);
}

function isSeniorLeadership(rank) {
  return getRankLevel(rank) >= RANKS.SSP.level;
}

/**
 * Validates jurisdictional ring-fencing.
 * Approvers must belong to the same police district/jurisdiction,
 * unless they are State-Level / Judicial Circuit officers or designated High/Critical senior leadership.
 */
function validateJurisdiction(requesterJurisdiction, approverJurisdiction, tier, approverRank) {
  if (!requesterJurisdiction || !approverJurisdiction) {
    return true; // Default fallback if jurisdiction is not configured
  }

  // Same district / ring-fenced
  if (requesterJurisdiction.toUpperCase() === approverJurisdiction.toUpperCase()) {
    return true;
  }

  // Cross-jurisdiction permitted for state-level or high judicial authorities
  if (STATE_WIDE_JURISDICTIONS.includes(approverJurisdiction.toUpperCase())) {
    return true;
  }

  // In HIGH or CRITICAL tier, senior leadership (Magistrate, FSL Head, SSP) may operate across districts
  if ((tier === 'HIGH' || tier === 'CRITICAL') && isSeniorLeadership(approverRank)) {
    return true;
  }

  return false;
}

/**
 * Performs complete assignment validation for an approver against the requester and tier constraints.
 */
function validateApproverEligibility(requester, approver, tierConfig) {
  // 1. Self-approval Hard Block
  if (requester.id === approver.id) {
    return {
      valid: false,
      code: 'SELF_APPROVAL_FORBIDDEN',
      message: `Self-approval violation: Officer '${approver.id}' cannot approve their own request.`
    };
  }

  // 2. Rank Hierarchy: Approvers chosen for pool N must ALWAYS be of equal or higher rank
  const requesterLevel = getRankLevel(requester.rank);
  const approverLevel = getRankLevel(approver.rank);

  if (approverLevel < requesterLevel) {
    return {
      valid: false,
      code: 'INSUFFICIENT_APPROVER_RANK',
      message: `Rank violation: Approver '${approver.id}' (${approver.rank} - Level ${approverLevel}) is junior to requester '${requester.id}' (${requester.rank} - Level ${requesterLevel}). Approvers must be of equal or higher rank.`
    };
  }

  // 3. Tier-Specific Minimum Rank (e.g. LOW requires local SHO or senior officer; CRITICAL requires Senior Leadership)
  if (tierConfig.min_approver_rank) {
    const minTierLevel = getRankLevel(tierConfig.min_approver_rank);
    if (approverLevel < minTierLevel) {
      return {
        valid: false,
        code: 'TIER_MINIMUM_RANK_NOT_MET',
        message: `Sensitivity tier '${tierConfig.tier}' requires approvers of at least rank '${tierConfig.min_approver_rank}' (Level ${minTierLevel}), but approver '${approver.id}' has rank '${approver.rank}' (Level ${approverLevel}).`
      };
    }
  }

  // 4. Jurisdictional Ring-fencing
  const hasValidJurisdiction = validateJurisdiction(
    requester.jurisdiction,
    approver.jurisdiction,
    tierConfig.tier,
    approver.rank
  );

  if (!hasValidJurisdiction) {
    return {
      valid: false,
      code: 'JURISDICTION_RINGFENCE_VIOLATION',
      message: `Jurisdictional violation: Approver '${approver.id}' belongs to district '${approver.jurisdiction}', which does not match requester's district '${requester.jurisdiction}' and does not qualify for state-level cross-jurisdiction review.`
    };
  }

  return { valid: true };
}

module.exports = {
  RANKS,
  STATE_WIDE_JURISDICTIONS,
  getRankLevel,
  isEqualOrHigherRank,
  isSeniorLeadership,
  validateJurisdiction,
  validateApproverEligibility
};
