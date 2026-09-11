import React, { useState } from 'react';
import { 
  X, 
  Check, 
  Circle, 
  CheckCircle2, 
  AlertCircle, 
  UserX, 
  ShieldAlert, 
  Sparkles,
  ArrowRight
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { translations } from '../i18n/translations';

/**
 * M-of-N Quorum Approval Modal — Simple Version per Master Spec Section 9
 * - Light-background card (NO dark backgrounds, NO glowing hexagons, NO sci-fi styling)
 * - Heading: "Approval Status"
 * - Plain numbered list: "Approver 1", "Approver 2", "Approver 3" (generic labels, NEVER real names)
 * - Empty circle (pending) or green checkmark (approved)
 * - Plain text: "X of Y approvals received"
 * - Simple horizontal progress bar (green fill on light-grey track)
 * - Rule 4B enforcement: If current user is requester, grey out & disable with tooltip:
 *   "Requester cannot approve own request" (also enforced 403 server-side)
 */
export default function QuorumModal({ 
  isOpen, 
  onClose, 
  document: doc, 
  activeUser, 
  onVoteSuccess, 
  onSwitchUser,
  lang = 'en'
}) {
  const t = translations[lang] || translations.en;
  const [comment, setComment] = useState('Reviewed against official case records. Approved for inclusion.');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen || !doc) return null;

  const session = doc.quorumSession || {
    docId: doc.id,
    version: doc.draftVersion || "1.1",
    status: "ACTIVE",
    threshold: 2,
    totalEligible: 3,
    approvalCount: 1,
    approversPool: [
      { id: "POL-IPS-1094", label: "Approver 1", title: "Supervisory Reviewer", pseudonym: "Approver_1", hasVoted: true, vote: "APPROVE", voteTime: "21/08/2024 10:30" },
      { id: "POL-SPS-2201", label: "Approver 2", title: "Review Board Member", pseudonym: "Approver_2", hasVoted: false, vote: null },
      { id: "PROS-HC-441", label: "Approver 3", title: "Public Prosecutor", pseudonym: "Approver_3", hasVoted: false, vote: null }
    ]
  };

  const isRequester = activeUser?.id === doc.requesterId;
  const thresholdMet = session.approvalCount >= session.threshold;
  const percentage = Math.round((session.approvalCount / session.threshold) * 100);

  const approverList = session.approversPool || [
    { label: "Approver 1", hasVoted: true },
    { label: "Approver 2", hasVoted: false },
    { label: "Approver 3", hasVoted: false }
  ];

  const handleVote = async (voteType = 'APPROVE') => {
    if (isRequester) {
      setErrorMsg("Requester cannot approve own request (Server-Enforced Rule 4B)");
      return;
    }

    setSubmitting(true);
    setErrorMsg('');

    try {
      const res = await fetch(`/api/documents/${doc.id}/quorum-vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          version: doc.draftVersion || "1.1",
          approverId: activeUser.id,
          vote: voteType,
          comment
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to cast vote");

      if (data.session && data.session.status === 'APPROVED') {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 }
        });
      }

      onVoteSuccess(data.document, data.session);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
      
      {/* Light Background Card */}
      <div className="bg-white border border-slate-200 rounded-3xl shadow-2xl max-w-lg w-full p-6 sm:p-8 space-y-6 animate-in zoom-in-95 duration-200 text-slate-800">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-orange-100 text-[#FF6A1A] border border-orange-200">
              M-of-N Consensus
            </span>
            <h3 className="text-lg font-bold text-slate-900 mt-1">
              {t.quorumHeading}
            </h3>
            <p className="text-xs text-slate-500">
              Docket Ref: <strong className="text-slate-700">{doc.firNo}</strong> • Draft v{doc.draftVersion || "1.1"}
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Section: Plain Numbered Approver List (Approver 1, Approver 2, Approver 3) */}
        <div className="space-y-3">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Designated Supervisory Reviewers
          </div>

          <div className="divide-y divide-slate-100 border border-slate-200 rounded-2xl overflow-hidden">
            {approverList.map((app, index) => {
              const label = app.label || `Approver ${index + 1}`;
              const isApproved = app.hasVoted && app.vote === 'APPROVE';

              return (
                <div 
                  key={index}
                  className="p-3.5 flex items-center justify-between bg-white hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    {/* Empty Circle or Green Checkmark */}
                    {isApproved ? (
                      <div className="w-6 h-6 rounded-full bg-emerald-100 text-[#5FA777] flex items-center justify-center">
                        <Check className="w-3.5 h-3.5 stroke-[3]" />
                      </div>
                    ) : (
                      <div className="w-6 h-6 rounded-full border-2 border-slate-300 flex items-center justify-center text-slate-300">
                        <Circle className="w-2.5 h-2.5" />
                      </div>
                    )}

                    <div>
                      <div className="text-xs font-bold text-slate-800">
                        {label}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {app.title || "Independent Supervisory Officer"}
                      </div>
                    </div>
                  </div>

                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                    isApproved 
                      ? 'bg-emerald-100 text-[#307044]' 
                      : 'bg-slate-100 text-slate-500'
                  }`}>
                    {isApproved ? 'Approved' : 'Pending'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Section: Plain Text Progress & Simple Horizontal Bar */}
        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold">
            <span className="text-slate-800">
              {session.approvalCount} of {session.threshold} {t.quorumThresholdLabel}
            </span>
            <span className={thresholdMet ? 'text-[#307044]' : 'text-[#FF6A1A]'}>
              {thresholdMet ? 'Threshold Satisfied' : `${percentage}% Completed`}
            </span>
          </div>

          {/* Simple Green Fill on Light-Grey Track */}
          <div className="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-[#5FA777] rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(5, percentage))}%` }}
            ></div>
          </div>
        </div>

        {/* Rule 4B Enforcement Notice: Requester cannot approve own request */}
        {isRequester && (
          <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-300 text-amber-900 text-xs flex items-start gap-2.5">
            <UserX className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="font-bold">Rule 4B Enforcement:</strong> Requester cannot approve own request. You are logged in as the Investigating Officer who initiated this amendment. Server-side API blocks self-approvals with 403 Forbidden.
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Action Controls */}
        {!thresholdMet ? (
          <div className="space-y-3 pt-2">
            {isRequester ? (
              <div className="text-center p-3 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
                <p className="text-xs text-slate-500">
                  Switch to an authorized supervisory reviewer to simulate quorum approval:
                </p>
                <div className="flex justify-center gap-2">
                  <button
                    onClick={() => onSwitchUser('POL-IPS-1094')}
                    className="px-3 py-1.5 bg-[#FF6A1A] hover:bg-[#E85B0E] text-white text-xs font-bold rounded-lg transition-colors cursor-pointer flex items-center gap-1"
                  >
                    <span>Switch to Approver 1</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => onSwitchUser('POL-SPS-2201')}
                    className="px-3 py-1.5 bg-[#4FA8E0] hover:bg-[#3B97D1] text-white text-xs font-bold rounded-lg transition-colors cursor-pointer flex items-center gap-1"
                  >
                    <span>Switch to Approver 2</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    {t.commentsLabel}
                  </label>
                  <input
                    type="text"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:outline-none focus:border-slate-400"
                  />
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleVote('APPROVE')}
                    disabled={submitting}
                    className="flex-1 py-2.5 bg-[#FF6A1A] hover:bg-[#E85B0E] text-white font-bold rounded-xl text-xs shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                  >
                    <Check className="w-4 h-4 stroke-[3]" />
                    <span>{submitting ? 'Submitting...' : t.castVoteApprove}</span>
                  </button>

                  <button
                    onClick={() => handleVote('REJECT')}
                    disabled={submitting}
                    className="px-4 py-2.5 bg-slate-100 hover:bg-red-50 text-slate-600 hover:text-red-600 border border-slate-300 rounded-xl text-xs font-bold transition-all cursor-pointer disabled:opacity-50"
                  >
                    <span>{t.castVoteReject}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-4 bg-emerald-50 border border-emerald-300 rounded-2xl text-center space-y-1">
            <div className="text-emerald-800 font-bold text-xs flex items-center justify-center gap-1.5">
              <Sparkles className="w-4 h-4 text-[#5FA777]" />
              <span>{t.consensusAchieved}</span>
            </div>
            <p className="text-[11px] text-emerald-700">
              The required 2-of-3 quorum consensus has been formally satisfied. Version 1.1 is now committed to head.
            </p>
          </div>
        )}

      </div>

    </div>
  );
}
