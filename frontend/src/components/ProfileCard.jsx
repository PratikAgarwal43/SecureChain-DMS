import React from 'react';
import {
  Shield,
  Scale,
  Microscope,
  ScrollText,
  User,
  Briefcase,
  ClipboardCheck,
  AlertCircle,
  FolderOpen,
  Clock,
  Settings,
  ChevronRight
} from 'lucide-react';

/**
 * ProfileCard — shared across all 5 roles.
 *
 * Props:
 *   activeUser    — logged-in user object from App state
 *   role          — 'POLICE' | 'JUDICIAL' | 'FORENSIC' | 'AUDITOR' | 'CITIZEN'
 *   documents     — full documents array (filtered internally per user)
 *   lang          — 'en' | 'hi'
 *   onGoToSettings — () => void  (navigates to settings tab)
 */
export default function ProfileCard({
  activeUser,
  role = 'POLICE',
  documents = [],
  lang = 'en',
  onGoToSettings
}) {
  if (!activeUser) return null;

  /* ── Role theme tokens ── */
  const THEMES = {
    POLICE: {
      accentBg: 'bg-orange-50 dark:bg-orange-950/40',
      accentBorder: 'border-orange-200 dark:border-orange-800',
      accentText: 'text-[#FF6A1A]',
      accentBadge: 'bg-orange-100 dark:bg-orange-900/60 text-[#FF6A1A] border border-orange-200 dark:border-orange-800',
      iconBg: 'bg-orange-100 dark:bg-orange-900/60',
      iconRing: 'ring-orange-200 dark:ring-orange-800',
      RoleIcon: Shield,
      roleLabel: 'Police / Investigating Officer',
      roleTag: 'POLICE'
    },
    JUDICIAL: {
      accentBg: 'bg-sky-50 dark:bg-sky-950/40',
      accentBorder: 'border-sky-200 dark:border-sky-800',
      accentText: 'text-[#4FA8E0]',
      accentBadge: 'bg-sky-100 dark:bg-sky-900/60 text-[#4FA8E0] border border-sky-200 dark:border-sky-800',
      iconBg: 'bg-sky-100 dark:bg-sky-900/60',
      iconRing: 'ring-sky-200 dark:ring-sky-800',
      RoleIcon: Scale,
      roleLabel: 'Judicial Authority Officer',
      roleTag: 'JUDICIAL'
    },
    FORENSIC: {
      accentBg: 'bg-emerald-50 dark:bg-emerald-950/40',
      accentBorder: 'border-emerald-200 dark:border-emerald-800',
      accentText: 'text-[#5FA777]',
      accentBadge: 'bg-emerald-100 dark:bg-emerald-900/60 text-[#5FA777] border border-emerald-200 dark:border-emerald-800',
      iconBg: 'bg-emerald-100 dark:bg-emerald-900/60',
      iconRing: 'ring-emerald-200 dark:ring-emerald-800',
      RoleIcon: Microscope,
      roleLabel: 'Forensic Science Officer',
      roleTag: 'FORENSIC'
    },
    AUDITOR: {
      accentBg: 'bg-purple-50 dark:bg-purple-950/40',
      accentBorder: 'border-purple-200 dark:border-purple-800',
      accentText: 'text-purple-600 dark:text-purple-400',
      accentBadge: 'bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800',
      iconBg: 'bg-purple-100 dark:bg-purple-900/60',
      iconRing: 'ring-purple-200 dark:ring-purple-800',
      RoleIcon: ScrollText,
      roleLabel: 'Statutory Auditor',
      roleTag: 'AUDITOR'
    },
    CITIZEN: {
      accentBg: 'bg-amber-50 dark:bg-amber-950/40',
      accentBorder: 'border-amber-200 dark:border-amber-800',
      accentText: 'text-amber-600 dark:text-amber-400',
      accentBadge: 'bg-amber-100 dark:bg-amber-900/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800',
      iconBg: 'bg-amber-100 dark:bg-amber-900/60',
      iconRing: 'ring-amber-200 dark:ring-amber-800',
      RoleIcon: User,
      roleLabel: 'Verified Citizen Complainant',
      roleTag: 'CITIZEN'
    }
  };

  const theme = THEMES[role] || THEMES.POLICE;
  const { RoleIcon, roleLabel, accentBg, accentBorder, accentText, accentBadge, iconBg, iconRing, roleTag } = theme;

  /* ── Identity line ── */
  const identityLine = (() => {
    const id = activeUser.id || activeUser.badge || '';
    switch (role) {
      case 'POLICE': {
        const station = activeUser.policeStation || activeUser.department || '';
        return `Police Official — Badge #${activeUser.badge || id}${station ? `, ${station}` : ''}`;
      }
      case 'JUDICIAL': {
        const court = activeUser.court || activeUser.department || '';
        return `Judicial Authority Officer — Judicial ID ${id}${court ? `, ${court}` : ''}`;
      }
      case 'FORENSIC': {
        const lab = activeUser.labUnit || activeUser.department || '';
        return `Forensic Science Officer — Lab ID ${id}${lab ? `, ${lab}` : ''}`;
      }
      case 'AUDITOR': {
        return `Statutory Auditor — Auditor ID ${id}`;
      }
      case 'CITIZEN': {
        const mobile = activeUser.mobile || '';
        const masked = mobile.length >= 6
          ? mobile.slice(0, 3) + '****' + mobile.slice(-3)
          : mobile;
        return `Citizen Complainant${masked ? ` — Mobile: ${masked}` : ''}`;
      }
      default:
        return roleLabel;
    }
  })();

  /* ── My Work snapshot — filtered strictly to this user's data ── */
  const myWork = (() => {
    const uid = activeUser.id;
    switch (role) {
      case 'POLICE': {
        const myCases = documents.filter(d => d.requesterId === uid);
        const myPending = myCases.filter(d => d.status === 'PENDING_QUORUM');
        return [
          { icon: FolderOpen, label: 'My Cases', value: myCases.length, desc: 'FIR records submitted by you' },
          { icon: Clock, label: 'Pending Quorum', value: myPending.length, desc: 'Awaiting multi-officer approval' }
        ];
      }
      case 'JUDICIAL': {
        const pendingApprovals = documents.filter(d => d.status === 'PENDING_QUORUM');
        return [
          { icon: ClipboardCheck, label: 'Pending Approvals', value: pendingApprovals.length, desc: 'Cases awaiting judicial review' }
        ];
      }
      case 'FORENSIC': {
        const myReports = documents.filter(d => d.requesterId === uid);
        const myPending = myReports.filter(d => d.status === 'PENDING_QUORUM');
        const allPending = documents.filter(d => d.status === 'PENDING_QUORUM');
        return [
          { icon: FolderOpen, label: 'My Reports', value: myReports.length, desc: 'Forensic reports authored by you' },
          { icon: Clock, label: 'My Pending', value: myPending.length, desc: 'Your submissions awaiting quorum' },
          { icon: ClipboardCheck, label: 'Quorum Queue', value: allPending.length, desc: 'All cases pending approval' }
        ];
      }
      case 'AUDITOR': {
        const pendingAny = documents.filter(d => d.status === 'PENDING_QUORUM');
        return [
          { icon: AlertCircle, label: 'Pending Reviews', value: pendingAny.length, desc: 'Cases pending override / review' },
          { icon: Briefcase, label: 'Total Records', value: documents.length, desc: 'Documents in ledger' }
        ];
      }
      case 'CITIZEN': {
        const linkedIds = activeUser.linkedCases || [];
        const myCases = documents.filter(d => linkedIds.includes(d.id));
        const active = myCases.filter(d => d.status !== 'REJECTED');
        return [
          { icon: FolderOpen, label: 'Linked Cases', value: myCases.length, desc: 'Case records linked to your complaint' },
          { icon: Clock, label: 'Active', value: active.length, desc: 'Currently under investigation' }
        ];
      }
      default:
        return [];
    }
  })();

  return (
    <div className={`${accentBg} border ${accentBorder} rounded-3xl p-5 sm:p-6 flex flex-col sm:flex-row gap-5 sm:items-start`}>

      {/* ── Left: Avatar + Identity ── */}
      <div className="flex items-start gap-4 flex-1 min-w-0">
        {/* Role silhouette icon — no photos, no external URLs */}
        <div className={`w-14 h-14 rounded-2xl ${iconBg} ring-2 ${iconRing} flex items-center justify-center flex-shrink-0`}>
          <RoleIcon className={`w-7 h-7 ${accentText}`} />
        </div>

        <div className="min-w-0 flex-1">
          {/* Role tag */}
          <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide ${accentBadge} mb-1.5`}>
            {roleTag}
          </span>

          {/* Role title */}
          <div className="text-sm font-bold text-slate-900 dark:text-slate-100 leading-tight">
            {roleLabel}
          </div>

          {/* Identity line — composed from login data */}
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-snug font-mono break-all sm:break-normal">
            {identityLine}
          </div>
        </div>
      </div>

      {/* ── Right: My Work snapshot + Settings link ── */}
      <div className="flex flex-col gap-3 sm:items-end sm:min-w-[200px]">
        {/* My Work counters */}
        {myWork.length > 0 && (
          <div className="flex flex-row sm:flex-col gap-2 flex-wrap sm:flex-nowrap">
            {myWork.map(({ icon: Icon, label, value, desc }) => (
              <div
                key={label}
                className="flex items-center gap-2.5 bg-white/70 dark:bg-slate-900/60 border border-white/80 dark:border-slate-700/60 rounded-2xl px-3 py-2 min-w-[120px] sm:min-w-[180px]"
                title={desc}
              >
                <div className={`w-7 h-7 rounded-xl ${iconBg} flex items-center justify-center flex-shrink-0`}>
                  <Icon className={`w-3.5 h-3.5 ${accentText}`} />
                </div>
                <div>
                  <div className="text-[17px] font-black text-slate-900 dark:text-slate-100 leading-none tabular-nums">
                    {value}
                  </div>
                  <div className="text-[10px] text-slate-500 dark:text-slate-400 font-semibold leading-none mt-0.5">
                    {label}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Settings link — quick-access only, full settings on Settings tab */}
        {onGoToSettings && (
          <button
            onClick={onGoToSettings}
            className={`inline-flex items-center gap-1.5 text-[11px] font-bold ${accentText} hover:opacity-80 transition-opacity cursor-pointer mt-1`}
          >
            <Settings className="w-3.5 h-3.5" />
            <span>Account Settings</span>
            <ChevronRight className="w-3 h-3" />
          </button>
        )}
      </div>

    </div>
  );
}
