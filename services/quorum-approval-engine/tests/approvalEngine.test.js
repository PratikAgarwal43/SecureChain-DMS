const request = require('supertest');
const createApp = require('../src/app');

describe('M-of-N Quorum Approval Engine - Core & Security Test Suite', () => {
  let app;
  let db;

  beforeEach(async () => {
    const created = createApp();
    app = created.app;
    db = created.db;

    // Seed test document
    await db.createDocument({
      id: 'doc_sec_101',
      title: 'Classified Architecture Spec',
      content: 'Version 1.0 Original Content',
      sensitivity_tier: 'HIGH',
      current_version: '1.0'
    });
  });

  describe('1. Quorum Logic & Sensitivity Tier Assignment', () => {
    test('Automatically assigns M=1, N=1 for LOW sensitivity tier', async () => {
      const res = await request(app)
        .post('/api/approval/requests')
        .send({
          documentId: 'doc_sec_101',
          requesterId: 'user_author_01',
          proposedContent: 'Updated LOW tier content',
          sensitivityTier: 'LOW',
          poolMemberIds: ['user_approver_99']
        });

      expect(res.status).toBe(201);
      expect(res.body.request.threshold_m).toBe(1);
      expect(res.body.request.pool_size_n).toBe(1);
      expect(res.body.request.status).toBe('PENDING');
    });

    test('Automatically assigns M=2, N=3 for MEDIUM sensitivity tier', async () => {
      const res = await request(app)
        .post('/api/approval/requests')
        .send({
          documentId: 'doc_sec_101',
          requesterId: 'user_author_01',
          proposedContent: 'Updated MEDIUM tier content',
          sensitivityTier: 'MEDIUM',
          poolMemberIds: ['user_app_1', 'user_app_2', 'user_app_3']
        });

      expect(res.status).toBe(201);
      expect(res.body.request.threshold_m).toBe(2);
      expect(res.body.request.pool_size_n).toBe(3);
    });

    test('Automatically assigns M=3, N=5 for HIGH sensitivity tier', async () => {
      const res = await request(app)
        .post('/api/approval/requests')
        .send({
          documentId: 'doc_sec_101',
          requesterId: 'user_author_01',
          proposedContent: 'Updated HIGH tier content',
          sensitivityTier: 'HIGH',
          poolMemberIds: ['user_app_1', 'user_app_2', 'user_app_3', 'user_app_4', 'user_app_5']
        });

      expect(res.status).toBe(201);
      expect(res.body.request.threshold_m).toBe(3);
      expect(res.body.request.pool_size_n).toBe(5);
    });

    test('Rejects request creation if pool member count does not match N requirement', async () => {
      const res = await request(app)
        .post('/api/approval/requests')
        .send({
          documentId: 'doc_sec_101',
          requesterId: 'user_author_01',
          proposedContent: 'Invalid pool count content',
          sensitivityTier: 'MEDIUM',
          poolMemberIds: ['user_app_1', 'user_app_2'] // 2 provided, 3 required
        });

      expect(res.status).toBe(400);
      expect(res.body.code).toBe('POOL_SIZE_MISMATCH');
    });
  });

  describe('2. Strict Security Constraints (Self-Approval Block & Duplicate Voting)', () => {
    test('Creation Guard: Rejects creation if requester ID is included in approval pool', async () => {
      const res = await request(app)
        .post('/api/approval/requests')
        .send({
          documentId: 'doc_sec_101',
          requesterId: 'user_author_01',
          proposedContent: 'Malicious self-approval attempt',
          sensitivityTier: 'MEDIUM',
          poolMemberIds: ['user_author_01', 'user_app_2', 'user_app_3']
        });

      expect(res.status).toBe(400);
      expect(res.body.code).toBe('REQUESTER_IN_APPROVAL_POOL');
    });

    test('Voting Guard: Hard backend block returning HTTP 403 when requester attempts self-approval', async () => {
      // Create request validly
      const createRes = await request(app)
        .post('/api/approval/requests')
        .send({
          documentId: 'doc_sec_101',
          requesterId: 'user_author_01',
          proposedContent: 'New sensitive patch',
          sensitivityTier: 'MEDIUM',
          poolMemberIds: ['user_app_1', 'user_app_2', 'user_app_3']
        });

      const requestId = createRes.body.request.id;

      // Attempt self-approval vote as requester
      const voteRes = await request(app)
        .post(`/api/approval/requests/${requestId}/vote`)
        .send({
          voterId: 'user_author_01', // Requester ID!
          voteChoice: 'APPROVE'
        });

      expect(voteRes.status).toBe(403);
      expect(voteRes.body.code).toBe('SELF_APPROVAL_FORBIDDEN');
      expect(voteRes.body.message).toContain('403 Forbidden');
    });

    test('Duplicate Vote Guard: Rejects second vote by the same approver with HTTP 409 Conflict', async () => {
      const createRes = await request(app)
        .post('/api/approval/requests')
        .send({
          documentId: 'doc_sec_101',
          requesterId: 'user_author_01',
          proposedContent: 'New sensitive patch',
          sensitivityTier: 'MEDIUM',
          poolMemberIds: ['user_app_1', 'user_app_2', 'user_app_3']
        });

      const requestId = createRes.body.request.id;

      // 1st vote by user_app_1
      const vote1 = await request(app)
        .post(`/api/approval/requests/${requestId}/vote`)
        .send({
          voterId: 'user_app_1',
          voteChoice: 'APPROVE'
        });
      expect(vote1.status).toBe(200);

      // 2nd vote by user_app_1
      const vote2 = await request(app)
        .post(`/api/approval/requests/${requestId}/vote`)
        .send({
          voterId: 'user_app_1',
          voteChoice: 'APPROVE'
        });

      expect(vote2.status).toBe(409);
      expect(vote2.body.code).toBe('DUPLICATE_VOTE');
    });
  });

  describe('3. Anonymous Approver Pool Logic', () => {
    test('API payload masks real user IDs and uses pseudonyms (Approver_XXXX)', async () => {
      const createRes = await request(app)
        .post('/api/approval/requests')
        .send({
          documentId: 'doc_sec_101',
          requesterId: 'user_author_01',
          proposedContent: 'Anonymous verification patch',
          sensitivityTier: 'MEDIUM',
          poolMemberIds: ['user_app_1', 'user_app_2', 'user_app_3']
        });

      const requestData = createRes.body.request;
      expect(requestData.approval_pool).toBeDefined();
      expect(requestData.approval_pool.length).toBe(3);

      // Verify no raw user IDs are exposed in the approval pool
      requestData.approval_pool.forEach((member) => {
        expect(member.approver_user_id).toBeUndefined();
        expect(member.pseudonym).toMatch(/^Approver_[A-Z0-9]{4}$/);
      });

      // Cast a vote and verify vote list is pseudonymized
      const requestId = requestData.id;
      const voteRes = await request(app)
        .post(`/api/approval/requests/${requestId}/vote`)
        .send({
          voterId: 'user_app_1',
          voteChoice: 'APPROVE'
        });

      const votes = voteRes.body.data.request.votes;
      expect(votes.length).toBe(1);
      expect(votes[0].voter_user_id).toBeUndefined();
      expect(votes[0].pseudonym).toMatch(/^Approver_[A-Z0-9]{4}$/);
    });
  });

  describe('4. State Management & Threshold Promotion & WORM Audit', () => {
    test('Incomplete Quorum Persistence: Request stays PENDING when votes < required M threshold', async () => {
      const createRes = await request(app)
        .post('/api/approval/requests')
        .send({
          documentId: 'doc_sec_101',
          requesterId: 'user_author_01',
          proposedContent: 'Incomplete Quorum Content',
          sensitivityTier: 'MEDIUM', // Threshold M=2
          poolMemberIds: ['user_app_1', 'user_app_2', 'user_app_3']
        });

      const requestId = createRes.body.request.id;

      // 1 vote cast out of 2 required
      const voteRes = await request(app)
        .post(`/api/approval/requests/${requestId}/vote`)
        .send({
          voterId: 'user_app_1',
          voteChoice: 'APPROVE'
        });

      expect(voteRes.status).toBe(200);
      expect(voteRes.body.data.request.status).toBe('PENDING');
      expect(voteRes.body.data.new_version).toBeNull();
    });

    test('Successful Threshold Promotion: Reaching M=2 updates status to APPROVED, creates Version 1.1, and logs WORM audit', async () => {
      const createRes = await request(app)
        .post('/api/approval/requests')
        .send({
          documentId: 'doc_sec_101',
          requesterId: 'user_author_01',
          proposedContent: 'Approved Document Patch v1.1 Content',
          sensitivityTier: 'MEDIUM', // M=2, N=3
          poolMemberIds: ['user_app_1', 'user_app_2', 'user_app_3']
        });

      const requestId = createRes.body.request.id;

      // Vote 1: APPROVE
      await request(app)
        .post(`/api/approval/requests/${requestId}/vote`)
        .send({ voterId: 'user_app_1', voteChoice: 'APPROVE' });

      // Vote 2: APPROVE (Reaches M=2 Quorum Threshold!)
      const voteRes2 = await request(app)
        .post(`/api/approval/requests/${requestId}/vote`)
        .send({ voterId: 'user_app_2', voteChoice: 'APPROVE' });

      expect(voteRes2.status).toBe(200);
      const data = voteRes2.body.data;
      expect(data.request.status).toBe('APPROVED');

      // Check document version bump
      expect(data.new_version).toBeDefined();
      expect(data.new_version.version_number).toBe('1.1');
      expect(data.new_version.content).toBe('Approved Document Patch v1.1 Content');

      // Verify Document updated in DB
      const updatedDoc = await db.getDocument('doc_sec_101');
      expect(updatedDoc.current_version).toBe('1.1');
      expect(updatedDoc.content).toBe('Approved Document Patch v1.1 Content');

      // Verify WORM Audit Log
      const auditRes = await request(app).get(`/api/approval/audit-logs?requestId=${requestId}`);
      expect(auditRes.status).toBe(200);
      const logs = auditRes.body.logs;
      expect(logs.some((l) => l.event_type === 'REQUEST_APPROVED')).toBe(true);
    });
  });
});
