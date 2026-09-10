import React, { useState, useEffect } from 'react';
import { 
  FileCheck2, 
  ShieldCheck, 
  AlertTriangle, 
  RefreshCw, 
  Lock, 
  FileText, 
  Search, 
  Database, 
  CheckCircle2, 
  XCircle,
  Download,
  Terminal,
  Layers,
  Fingerprint,
  KeyRound,
  Eye,
  AlertCircle,
  ArrowRight,
  Clock,
  UserCheck,
  Building2,
  Check,
  ShieldAlert
} from 'lucide-react';
import { translations } from '../../i18n/translations';
import { useToast } from '../../context/ToastContext';
import AuditLogView from '../AuditLogView';
import RoleSettingsPanel from '../../components/RoleSettingsPanel';
import ProfileCard from '../../components/ProfileCard';


export default function AuditorDashboard({ 
  activeUser, 
  activeTab = 'overview',
  onSelectTab,
  onNavigateToTab,
  lang = 'en',
  darkMode = false,
  onToggleDark,
  onToggleLang
}) {
  const t = translations[lang] || translations.en;
  const toast = useToast();

  const [currentTab, setCurrentTab] = useState(activeTab);
  useEffect(() => {
    if (activeTab) setCurrentTab(activeTab);
  }, [activeTab]);

  const [integrityStatus, setIntegrityStatus] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [tampering, setTampering] = useState(false);
  const [restoring, setRestoring] = useState(false);

  // De-anonymization form state
  const [pseudoInput, setPseudoInput] = useState('Approver_1094');
  const [justificationInput, setJustificationInput] = useState('');
  const [caseRefInput, setCaseRefInput] = useState('FIR-2024-ND-0842');
  const [deAnonymizeLoading, setDeAnonymizeLoading] = useState(false);
  const [revealedResult, setRevealedResult] = useState(null);
  // Inline field error for the justification textarea
  const [justificationFieldError, setJustificationFieldError] = useState('');

  const [deAnonymizeHistory, setDeAnonymizeHistory] = useState([
    {
      id: 'DEANON-901',
      pseudonym: 'Approver_2201',
      revealedId: 'POL-SPS-2201 (Police Official - Superintendent of Police, Crime Branch)',
      justification: 'High Court Writ Petition HC/WP-2819/2024 ordering officer disclosure in bail scrutiny',
      timestamp: '2024-09-02T14:22:00Z',
      auditor: 'Auditor Official (Statutory Audit Authority)'
    }
  ]);

  // Emergency Override Queue state
  const [emergencyOverrides, setEmergencyOverrides] = useState([
    {
      id: 'EMG-2024-0842',
      caseRef: 'FIR-2024-ND-0842',
      title: 'State vs Syndicate Banking Fraud',
      tier: 'HIGH',
      reason: 'Urgent seizure order compliance under PMLA Section 17; fast-track bypass authorized',
      invokedBy: 'Police Official (IO Badge #1042)',
      timestamp: '2024-09-03T11:45:00Z',
      status: 'AWAITING_REVIEW'
    },
    {
      id: 'EMG-2024-1920',
      caseRef: 'FIR-2024-MH-1920',
      title: 'Power Grid SCADA Infiltration Evidence',
      tier: 'HIGH',
      reason: 'Critical infrastructure immediate preservation warrant; statutory 6-hour window',
      invokedBy: 'Forensic Officer (Principal Custodian #702)',
      timestamp: '2024-09-03T18:10:00Z',
      status: 'AWAITING_REVIEW'
    }
  ]);

  // Fetch initial integrity status
  const runIntegrityVerification = async () => {
    setVerifying(true);
    try {
      const res = await fetch('/api/tamper/verify', { method: 'POST' });
      const data = await res.json();
      setIntegrityStatus(data);
      if (data.status === 'TAMPERED') {
        toast.error(`Ledger Compromise Detected at Block #${data.tamperedBlockIndex || 'UNKNOWN'}`);
      } else {
        toast.success('SHA-256 Merkle Chain Integrity Confirmed: 100% Pristine');
      }
    } catch (err) {
      toast.error('Integrity verification network error.');
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    runIntegrityVerification();
  }, []);

  const handleSimulateTamper = async () => {
    setTampering(true);
    try {
      const res = await fetch('/api/tamper/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          docId: 'FIR-2024-ND-0842',
          tamperedText: 'ILLEGAL UNAUTHORIZED RECORD MODIFICATION VIA DIRECT DB ACCESS'
        })
      });
      const data = await res.json();
      toast.warning('Tamper simulation executed! Layer 6 Sentinel triggered.');
      runIntegrityVerification();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setTampering(false);
    }
  };

  const handleRestoreIntegrity = async () => {
    setRestoring(true);
    try {
      const res = await fetch('/api/tamper/restore', { method: 'POST' });
      const data = await res.json();
      toast.success('Ledger state restored from pristine cryptographic anchor.');
      runIntegrityVerification();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setRestoring(false);
    }
  };

  const handleDeAnonymizeSubmit = async (e) => {
    e.preventDefault();
    if (!justificationInput || justificationInput.trim().length < 15) {
      setJustificationFieldError('Statutory Justification must be at least 15 characters under IT Act §65B / Rule 12.');
      toast.error('Statutory Justification must be at least 15 characters long under IT Act §65B / Rule 12.');
      return;
    }
    setJustificationFieldError('');

    setDeAnonymizeLoading(true);
    try {
      const res = await fetch('/api/deanonymize', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-employee-id': activeUser?.employeeId || 'AUD-MHA-007'
        },
        body: JSON.stringify({
          pseudonym: pseudoInput.trim(),
          justification: justificationInput.trim()
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'De-anonymization failed');

      setRevealedResult(data);
      toast.success(`Identity disclosed: ${data.realIdentity?.employeeId || 'DISCLOSED'}. Action logged into WORM vault.`);
      
      setDeAnonymizeHistory(prev => [
        {
          id: `DEANON-${Math.floor(1000 + Math.random() * 9000)}`,
          pseudonym: pseudoInput,
          revealedId: `${data.realIdentity?.employeeId || 'IDENTIFIED'} (${data.realIdentity?.role || 'Police Official'})`,
          justification: justificationInput,
          timestamp: new Date().toISOString(),
          auditor: 'Auditor Official (Statutory Audit Authority)'
        },
        ...prev
      ]);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setDeAnonymizeLoading(false);
    }
  };

  const handleReviewOverride = (id, approved) => {
    setEmergencyOverrides(prev => prev.map(o => {
      if (o.id === id) {
        return { ...o, status: approved ? 'CONFIRMED_LEGITIMATE' : 'FLAGGED_FOR_INQUIRY' };
      }
      return o;
    }));
    if (approved) {
      toast.success(`Emergency Override ${id} confirmed legitimate and sealed in statutory archive.`);
    } else {
      toast.error(`Emergency Override ${id} flagged for disciplinary inquiry! Action recorded.`);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-300 w-full">
      
      {/* Auditor Header Banner */}
      <div className="bg-white dark:bg-slate-900 border border-purple-200 dark:border-slate-800 rounded-3xl p-4 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6 w-full transition-colors">
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-2xl bg-purple-100 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center flex-shrink-0 shadow-xs border border-purple-200 dark:border-purple-800">
            <FileCheck2 className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-purple-100 dark:bg-purple-950 text-purple-800 dark:text-purple-300 border border-purple-300 dark:border-purple-800">
                Statutory Oversight & Cryptographic Audit
              </span>
              <span className="text-xs text-slate-400 font-mono">Auditor-Restricted Vault</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
              WORM Immutable Audit Vault & Chain Sentinel
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-2xl">
              Strictly append-only write-once read-many ledger per Ministry of Home Affairs Electronic Evidence Standards. Only the Auditor authority can inspect this audit trail.
            </p>
          </div>
        </div>

        {/* Auditor Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={runIntegrityVerification}
            disabled={verifying}
            className="px-3.5 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
            <span>Verify Merkle Chain</span>
          </button>

          {integrityStatus?.status === 'TAMPERED' ? (
            <button
              onClick={handleRestoreIntegrity}
              disabled={restoring}
              className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Restore Pristine Ledger</span>
            </button>
          ) : (
            <button
              onClick={handleSimulateTamper}
              disabled={tampering}
              className="px-3 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-slate-700 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 text-xs font-bold rounded-xl border border-slate-200 dark:border-slate-700 transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              title="Demonstrate real-time cryptographic tamper alarm"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
              <span>Simulate DB Tampering</span>
            </button>
          )}
        </div>
      </div>

      {/* VIEW: OVERVIEW / HOME */}
      {(currentTab === 'overview' || currentTab === 'home') && (
        <div className="space-y-6 animate-in fade-in">
          
          {/* Profile Card — identity + My Work snapshot */}
          <ProfileCard
            activeUser={activeUser}
            role="AUDITOR"
            documents={documents}
            lang={lang}
            onGoToSettings={() => setCurrentTab('settings')}
          />

          {/* Cryptographic Health Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Chain Integrity */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-purple-300 dark:hover:border-purple-700 rounded-3xl p-5 shadow-xs transition-all duration-200 hover:-translate-y-1 hover:shadow-lg group">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                <span className="font-semibold">Ledger Health</span>
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${
                  integrityStatus?.status === 'TAMPERED' 
                    ? 'bg-rose-100 text-rose-600 dark:bg-rose-950 dark:text-rose-400' 
                    : 'bg-emerald-100 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400'
                }`}>
                  {integrityStatus?.status === 'TAMPERED' ? <XCircle className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                </div>
              </div>
              <div className="mt-2">
                <div className={`text-xl font-bold tracking-tight ${
                  integrityStatus?.status === 'TAMPERED' ? 'text-rose-600' : 'text-emerald-600'
                }`}>
                  {integrityStatus?.status === 'TAMPERED' ? 'COMPROMISED' : 'PRISTINE SECURE'}
                </div>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                  {integrityStatus?.message || 'SHA-256 Merkle Chain Active'}
                </p>
              </div>
            </div>

            {/* Card 2: Total WORM Blocks */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-purple-300 dark:hover:border-purple-700 rounded-3xl p-5 shadow-xs transition-all duration-200 hover:-translate-y-1 hover:shadow-lg group">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                <span className="font-semibold">Audit Blocks Sealed</span>
                <div className="w-8 h-8 rounded-xl bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                  <Database className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {integrityStatus?.totalBlocks || '18'}
                </div>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                  Zero deletions / zero rewrites
                </p>
              </div>
            </div>

            {/* Card 3: Security Layers Monitored */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-purple-300 dark:hover:border-purple-700 rounded-3xl p-5 shadow-xs transition-all duration-200 hover:-translate-y-1 hover:shadow-lg group">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                <span className="font-semibold">Security Layers</span>
                <div className="w-8 h-8 rounded-xl bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                  <Layers className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  6 / 6
                </div>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                  Active WORM sentinel protection
                </p>
              </div>
            </div>

            {/* Card 4: Emergency Overrides */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-purple-300 dark:hover:border-purple-700 rounded-3xl p-5 shadow-xs transition-all duration-200 hover:-translate-y-1 hover:shadow-lg group">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                <span className="font-semibold">Emergency Overrides</span>
                <div className="w-8 h-8 rounded-xl bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                  <ShieldAlert className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <div className="text-2xl font-bold text-amber-600">
                  {emergencyOverrides.filter(o => o.status === 'AWAITING_REVIEW').length}
                </div>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                  Pending post-hoc scrutiny
                </p>
              </div>
            </div>
          </div>

          {/* Embedded Full Audit Trail Preview */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100">
                  Real-Time WORM Audit Stream
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Live cryptographic activity stream recorded in write-once read-many ledger.
                </p>
              </div>
            </div>
            <AuditLogView lang={lang} activeUser={activeUser} />
          </div>
        </div>
      )}

      {/* VIEW: WORM AUDIT LOG */}
      {(currentTab === 'audit' || currentTab === 'worm') && (
        <div className="space-y-4 animate-in fade-in">
          <AuditLogView lang={lang} activeUser={activeUser} />
        </div>
      )}

      {/* VIEW: DE-ANONYMIZE REQUESTS */}
      {currentTab === 'deanonymize' && (
        <div className="space-y-6 animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 border border-purple-200 dark:border-purple-900/60 rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-purple-100 dark:bg-purple-950 text-purple-800 dark:text-purple-300 border border-purple-300 dark:border-purple-800">
                  Statutory Rule 12 Protocol
                </span>
                <span className="text-xs text-slate-400 font-mono">Auditor Sole Authority</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1">
                Cryptographic De-Anonymization Request Terminal
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">
                By statutory mandate under Evidence Act §65B and Ministry of Home Affairs rules, approver identities are masked by default to eliminate peer coercion. Only an authorized Statutory Auditor can disclose the officer behind a pseudonym upon submitting a legally documented justification. Every disclosure is itself permanently sealed in the WORM audit trail.
              </p>
            </div>

            {/* Submission Form */}
            <form onSubmit={handleDeAnonymizeSubmit} className="space-y-4 max-w-2xl">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Pseudonymous Approver ID *
                  </label>
                  <input
                    type="text"
                    value={pseudoInput}
                    onChange={(e) => setPseudoInput(e.target.value)}
                    placeholder="e.g. Approver_1094, Approver_X7A2"
                    className="w-full px-3.5 py-2.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl font-mono text-slate-900 dark:text-slate-100 focus:outline-none focus:border-purple-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Target Docket / FIR Reference *
                  </label>
                  <input
                    type="text"
                    value={caseRefInput}
                    onChange={(e) => setCaseRefInput(e.target.value)}
                    placeholder="e.g. FIR-2024-ND-0842"
                    className="w-full px-3.5 py-2.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl font-mono text-slate-900 dark:text-slate-100 focus:outline-none focus:border-purple-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Mandatory Statutory Justification (Court Order / Section 65B Writ Ref) *
                </label>
                <textarea
                  rows={3}
                  value={justificationInput}
                  onChange={(e) => { setJustificationInput(e.target.value); if (e.target.value.trim().length >= 15) setJustificationFieldError(''); }}
                  onBlur={(e) => {
                    if (e.target.value.trim().length > 0 && e.target.value.trim().length < 15) {
                      setJustificationFieldError('Statutory Justification must be at least 15 characters under IT Act §65B / Rule 12.');
                    }
                  }}
                  placeholder="Enter court reference, trial order number, or statutory audit rationale requiring identity disclosure..."
                  className={`w-full px-3.5 py-2.5 text-xs bg-slate-50 dark:bg-slate-800 border rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-purple-500 ${
                    justificationFieldError ? 'border-rose-400 dark:border-rose-600' : 'border-slate-300 dark:border-slate-700'
                  }`}
                  required
                />
                {justificationFieldError ? (
                  <p className="text-[10px] text-rose-600 dark:text-rose-400 mt-0.5 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3 flex-shrink-0" />
                    {justificationFieldError}
                  </p>
                ) : (
                  <span className="text-[10px] text-slate-400">Minimum 15 characters required. This rationale will be permanently recorded in the ledger.</span>
                )}
              </div>


              <button
                type="submit"
                disabled={deAnonymizeLoading}
                className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <KeyRound className="w-4 h-4" />
                <span>{deAnonymizeLoading ? 'Executing Statutory Decryption...' : 'Execute Statutory De-Anonymization'}</span>
              </button>
            </form>

            {/* Revealed Result Card */}
            {revealedResult && (
              <div className="p-5 rounded-2xl bg-purple-50 dark:bg-purple-950/50 border-2 border-purple-400 dark:border-purple-700 space-y-3 animate-in fade-in">
                <div className="flex items-center gap-2 text-purple-900 dark:text-purple-200 text-xs font-bold">
                  <CheckCircle2 className="w-4 h-4 text-purple-600" />
                  <span>Statutory Disclosure Authorized & Anchored in WORM Log</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-[10px]">Pseudonym</span>
                    <strong className="font-mono text-purple-800 dark:text-purple-300">{revealedResult.pseudonym}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-[10px]">Decrypted Official ID</span>
                    <strong className="font-mono text-slate-900 dark:text-slate-100">{revealedResult.realIdentity?.employeeId || 'POL-IPS-1094'}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-[10px]">Official Role Title</span>
                    <strong className="text-slate-900 dark:text-slate-100">{revealedResult.realIdentity?.role || 'Police Official (Supervisory Inspector)'}</strong>
                  </div>
                </div>
                <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 pt-2 border-t border-purple-200 dark:border-purple-800">
                  WORM Transaction Hash: <span className="text-purple-700 dark:text-purple-300">{revealedResult.wormTransactionHash || '3d5f8a0e889c2b4c10294e77da1b1c3e'}</span>
                </div>
              </div>
            )}
          </div>

          {/* Past De-Anonymization Disclosures Table */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs space-y-4">
            <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              Statutory Disclosure Audit Trail (Past Requests)
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300">
                  <tr>
                    <th className="p-3">Reference ID</th>
                    <th className="p-3">Masked Pseudonym</th>
                    <th className="p-3">Disclosed Officer ID</th>
                    <th className="p-3">Legal Justification</th>
                    <th className="p-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                  {deAnonymizeHistory.map(item => (
                    <tr key={item.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                      <td className="p-3 font-mono text-purple-600 dark:text-purple-400 font-bold">{item.id}</td>
                      <td className="p-3 font-mono">{item.pseudonym}</td>
                      <td className="p-3 font-bold">{item.revealedId}</td>
                      <td className="p-3 text-slate-600 dark:text-slate-400 max-w-xs truncate" title={item.justification}>{item.justification}</td>
                      <td className="p-3 font-mono text-[11px] text-slate-500">{new Date(item.timestamp).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* VIEW: EMERGENCY OVERRIDE REVIEW */}
      {currentTab === 'override' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                Post-Hoc Scrutiny Queue
              </span>
              <span className="text-xs text-slate-400 font-mono">Emergency Provisions</span>
            </div>
            <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 mt-1">
              Emergency Override Scrutiny Board
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Under urgent operational constraints, IOs may invoke an emergency fast-track. All such events are queued here for mandatory post-hoc statutory audit and disciplinary verification.
            </p>
          </div>

          <div className="space-y-4">
            {emergencyOverrides.map(item => (
              <div 
                key={item.id}
                className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold bg-white dark:bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100">
                      {item.id}
                    </span>
                    <span className="text-xs font-bold text-purple-600 dark:text-purple-400 font-mono">
                      {item.caseRef}
                    </span>
                  </div>

                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                    item.status === 'AWAITING_REVIEW'
                      ? 'bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800'
                      : item.status === 'CONFIRMED_LEGITIMATE'
                      ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800'
                      : 'bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800'
                  }`}>
                    {item.status.replace(/_/g, ' ')}
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{item.title}</h4>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                    <strong>Operational Reason:</strong> {item.reason}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-200 dark:border-slate-700/60 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="text-slate-500 dark:text-slate-400 text-[11px]">
                    Invoked by: <strong>{item.invokedBy}</strong> • Time: {new Date(item.timestamp).toLocaleString()}
                  </div>

                  {item.status === 'AWAITING_REVIEW' && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleReviewOverride(item.id, false)}
                        className="px-3 py-1.5 bg-rose-50 dark:bg-rose-950/50 hover:bg-rose-100 text-rose-700 dark:text-rose-300 font-bold rounded-xl text-xs border border-rose-200 dark:border-rose-800 cursor-pointer"
                      >
                        Flag for Disciplinary Inquiry
                      </button>
                      <button
                        onClick={() => handleReviewOverride(item.id, true)}
                        className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs shadow-xs cursor-pointer"
                      >
                        Confirm Statutory Legitimacy
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* VIEW: VERIFY INTEGRITY (SYSTEM-WIDE) */}
      {currentTab === 'verify' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
            <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100">
              System-Wide Merkle Chain & Ledger Integrity Scanner
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Recomputes cryptographic hashes across every block in the WORM chain to ensure zero byte mutations have occurred.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  integrityStatus?.status === 'TAMPERED'
                    ? 'bg-rose-100 text-rose-600 dark:bg-rose-950 dark:text-rose-400'
                    : 'bg-emerald-100 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400'
                }`}>
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    Chain Health: {integrityStatus?.status === 'TAMPERED' ? 'INTEGRITY COMPROMISE DETECTED' : '100% PRISTINE & UNMODIFIED'}
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {integrityStatus?.totalBlocks || 18} Blocks Verified Against Hardware Root Anchor
                  </p>
                </div>
              </div>

              <button
                onClick={runIntegrityVerification}
                disabled={verifying}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
                <span>Re-Verify Whole Chain</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs pt-3 border-t border-slate-200 dark:border-slate-700 font-mono">
              <div><strong>Root Anchor:</strong> 0000000000000000000000000000000000000000000000000000000000000000</div>
              <div><strong>Algorithm:</strong> SHA-256 (FIPS 180-4)</div>
              <div><strong>Audit Standard:</strong> IT Act Section 65B(4)</div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW: SETTINGS */}
      {currentTab === 'settings' && (
        <RoleSettingsPanel
          activeUser={activeUser}
          role="AUDITOR"
          lang={lang}
          darkMode={darkMode}
          onToggleDark={onToggleDark}
          onToggleLang={onToggleLang}
        />
      )}

    </div>
  );
}
