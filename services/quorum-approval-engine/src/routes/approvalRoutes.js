const express = require('express');

function createApprovalRoutes(approvalController) {
  const router = express.Router();

  // Helper document creation
  router.post('/documents', approvalController.createDocument);

  // Edit Request Management
  router.post('/requests', approvalController.createRequest);
  router.get('/requests/:id', approvalController.getRequestDetails);
  router.post('/requests/:id/vote', approvalController.vote);

  // WORM Audit Logs
  router.get('/audit-logs', approvalController.getAuditLogs);

  return router;
}

module.exports = createApprovalRoutes;
