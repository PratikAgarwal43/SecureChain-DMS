import React, { useState } from 'react';
import {
  User,
  Lock,
  Bell,
  Globe,
  Sun,
  Moon,
  Eye,
  EyeOff,
  Shield,
  Scale,
  Microscope,
  ScrollText,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

/**
 * RoleSettingsPanel — shared across Police, Judicial, Forensic, Auditor dashboards.
 *
 * Props:
 *   activeUser   — logged-in user object from App state
 *   role         — 'POLICE' | 'JUDICIAL' | 'FORENSIC' | 'AUDITOR'
 *   lang         — 'en' | 'hi'
 *   darkMode     — boolean (current dark mode state)
 *   onToggleDark — () => void  (fires the App-level dark mode toggle)
 *   onToggleLang — () => void  (fires the App-level language toggle)
 */
export default function RoleSettingsPanel({
  activeUser,
  role = 'POLICE',
  lang = 'en',
  darkMode = false,
  onToggleDark,
  onToggleLang
}) {
  /* ── Change Password local state ── */
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [pwMsg, setPwMsg] = useState(null); // { type: 'success'|'error', text }

  /* ── Notification Preferences local state ── */
  const [notifPrefs, setNotifPrefs] = useState({
    emailPendingApprovals: true,
    smsPendingApprovals: false,
    emailEditUpdates: true,
    smsEditUpdates: false,
    emailSystemAlerts: true
  });
  const toggleNotif = (key) =>
    setNotifPrefs((prev) => ({ ...prev, [key]: !prev[key] }));

  /* ── Role theme tokens ── */
  const THEMES = {
    POLICE: {
      accentBg: 'bg-orange-100 dark:bg-orange-950',
      accentText: 'text-[#FF6A1A]',
      accentBorder: 'border-orange-200 dark:border-orange-800',
      accentBtnCls: 'bg-[#FF6A1A] hover:bg-[#e05910]',
      tag: 'bg-orange-100 dark:bg-orange-950 text-[#FF6A1A] border border-orange-200 dark:border-orange-800',
      RoleIcon: Shield,
      roleLabel: 'Police / Investigating Officer'
    },
    JUDICIAL: {
      accentBg: 'bg-sky-100 dark:bg-sky-950',
      accentText: 'text-[#4FA8E0]',
      accentBorder: 'border-sky-200 dark:border-sky-800',
      accentBtnCls: 'bg-[#4FA8E0] hover:bg-[#3B97D1]',
      tag: 'bg-sky-100 dark:bg-sky-950 text-[#4FA8E0] border border-sky-200 dark:border-sky-800',
      RoleIcon: Scale,
      roleLabel: 'Judicial Authority Officer'
    },
    FORENSIC: {
      accentBg: 'bg-emerald-100 dark:bg-emerald-950',
      accentText: 'text-[#5FA777]',
      accentBorder: 'border-emerald-200 dark:border-emerald-800',
      accentBtnCls: 'bg-[#5FA777] hover:bg-[#4e8f65]',
      tag: 'bg-emerald-100 dark:bg-emerald-950 text-[#5FA777] border border-emerald-200 dark:border-emerald-800',
      RoleIcon: Microscope,
      roleLabel: 'Forensic Science Officer'
    },
    AUDITOR: {
      accentBg: 'bg-purple-100 dark:bg-purple-950',
      accentText: 'text-purple-600 dark:text-purple-400',
      accentBorder: 'border-purple-200 dark:border-purple-800',
      accentBtnCls: 'bg-purple-600 hover:bg-purple-700',
      tag: 'bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800',
      RoleIcon: ScrollText,
      roleLabel: 'Statutory Auditor'
    }
  };

  const theme = THEMES[role] || THEMES.POLICE;
  const { RoleIcon, roleLabel, accentBtnCls, accentText, accentBg, accentBorder, tag } = theme;

  /* ── Profile fields per role — generic title, no invented names ── */
  const profileRows = (() => {
    switch (role) {
      case 'POLICE':
        return [
          { label: 'Role', value: roleLabel },
          { label: 'Badge / Employee ID', value: activeUser?.badgeId || activeUser?.id || 'POLICE-OFFICER' },
          { label: 'Police Station', value: activeUser?.policeStation || 'Special Investigation Division PS' }
        ];
      case 'JUDICIAL':
        return [
          { label: 'Role', value: roleLabel },
          { label: 'Judicial ID', value: activeUser?.judicialId || activeUser?.id || 'JUDICIAL-OFFICER' },
          { label: 'Court / Jurisdiction', value: activeUser?.court || 'Patiala House Courts, New Delhi' }
        ];
      case 'FORENSIC':
        return [
          { label: 'Role', value: roleLabel },
          { label: 'Lab ID', value: activeUser?.labId || activeUser?.id || 'FORENSIC-OFFICER' },
          { label: 'Lab / Unit', value: activeUser?.labUnit || 'NABL Forensic Science Laboratory' }
        ];
      case 'AUDITOR':
        return [
          { label: 'Role', value: roleLabel },
          { label: 'Auditor ID', value: activeUser?.auditorId || activeUser?.id || 'AUDITOR-OFFICER' },
          { label: 'Authority', value: 'Statutory Audit Authority — GOI' }
        ];
      default:
        return [
          { label: 'Role', value: roleLabel },
          { label: 'ID', value: activeUser?.id || role }
        ];
    }
  })();

  /* ── Change Password submit ── */
  const handlePwSubmit = (e) => {
    e.preventDefault();
    if (!currentPw) {
      setPwMsg({ type: 'error', text: 'Please enter your current password.' });
      return;
    }
    if (newPw.length < 8) {
      setPwMsg({ type: 'error', text: 'New password must be at least 8 characters.' });
      return;
    }
    if (newPw !== confirmPw) {
      setPwMsg({ type: 'error', text: 'New password and confirmation do not match.' });
      return;
    }
    setPwMsg({ type: 'success', text: 'Password updated successfully.' });
    setCurrentPw('');
    setNewPw('');
    setConfirmPw('');
  };

  /* ── Sub-components ── */
  const SectionHeader = ({ icon: Icon, title, subtitle }) => (
    <div className="flex items-start gap-3 border-b border-slate-100 dark:border-slate-800 pb-4 mb-5">
      <div className={`w-9 h-9 rounded-xl ${accentBg} border ${accentBorder} flex items-center justify-center flex-shrink-0 mt-0.5`}>
        <Icon className={`w-4 h-4 ${accentText}`} />
      </div>
      <div>
        <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{title}</h4>
        {subtitle && <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );

  const Toggle = ({ checked, onChange, id }) => (
    <button
      id={id}
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none ${
        checked ? accentBtnCls.split(' ')[0] : 'bg-slate-300 dark:bg-slate-600'
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200 ${
          checked ? 'translate-x-4' : 'translate-x-0'
        }`}
      />
    </button>
  );

  const PwField = ({ id, label, value, onChange, show, onToggleShow }) => (
    <div>
      <label htmlFor={id} className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={show ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3.5 py-2.5 pr-10 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-slate-400 dark:focus:border-slate-500 placeholder-slate-400"
          placeholder="••••••••"
        />
        <button
          type="button"
          onClick={onToggleShow}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          {show ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>
  );

  /* ── Render ── */
  return (
    <div className="space-y-6 animate-in fade-in w-full">

      {/* Page heading */}
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-2xl ${accentBg} border ${accentBorder} flex items-center justify-center`}>
          <RoleIcon className={`w-5 h-5 ${accentText}`} />
        </div>
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 font-serif">Settings</h3>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">Account preferences and portal configuration</p>
        </div>
        <span className={`ml-auto px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${tag}`}>
          {role}
        </span>
      </div>

      {/* ── 1. Profile ── */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs">
        <SectionHeader
          icon={User}
          title="Profile"
          subtitle="Read-only display of your registered identity on this portal"
        />
        <dl className="space-y-0">
          {profileRows.map(({ label, value }) => (
            <div
              key={label}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 py-2.5 border-b border-slate-100 dark:border-slate-800 last:border-0"
            >
              <dt className="text-xs font-semibold text-slate-500 dark:text-slate-400 min-w-[180px]">{label}</dt>
              <dd className="text-xs font-bold text-slate-900 dark:text-slate-100 font-mono sm:text-right">{value}</dd>
            </div>
          ))}
        </dl>
        <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-4">
          Identity fields are provisioned by the Ministry of Home Affairs administrator. Contact your system admin to update registered details.
        </p>
      </div>

      {/* ── 2. Change Password ── */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs">
        <SectionHeader
          icon={Lock}
          title="Change Password"
          subtitle="Update your login credential. Minimum 8 characters required."
        />
        <form onSubmit={handlePwSubmit} className="space-y-4 max-w-md">
          <PwField
            id="settings-current-pw"
            label="Current Password"
            value={currentPw}
            onChange={setCurrentPw}
            show={showCurrent}
            onToggleShow={() => setShowCurrent((v) => !v)}
          />
          <PwField
            id="settings-new-pw"
            label="New Password"
            value={newPw}
            onChange={setNewPw}
            show={showNew}
            onToggleShow={() => setShowNew((v) => !v)}
          />
          <PwField
            id="settings-confirm-pw"
            label="Confirm New Password"
            value={confirmPw}
            onChange={setConfirmPw}
            show={showConfirm}
            onToggleShow={() => setShowConfirm((v) => !v)}
          />

          {pwMsg && (
            <div className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold ${
              pwMsg.type === 'success'
                ? 'bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300'
                : 'bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-300'
            }`}>
              {pwMsg.type === 'success'
                ? <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
              {pwMsg.text}
            </div>
          )}

          <button
            type="submit"
            className={`px-5 py-2.5 ${accentBtnCls} text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer`}
          >
            Update Password
          </button>
        </form>
      </div>

      {/* ── 3. Notification Preferences ── */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs">
        <SectionHeader
          icon={Bell}
          title="Notification Preferences"
          subtitle="Choose how you want to be alerted for key portal events"
        />
        <div className="space-y-0 max-w-lg">
          {[
            {
              key: 'emailPendingApprovals',
              label: 'Email — Pending Approval Alerts',
              desc: 'Receive email when a quorum vote awaits your action'
            },
            {
              key: 'smsPendingApprovals',
              label: 'SMS — Pending Approval Alerts',
              desc: 'Receive SMS when a quorum vote awaits your action'
            },
            {
              key: 'emailEditUpdates',
              label: 'Email — Edit Request Status Updates',
              desc: 'Get notified when your submitted amendment docket changes status'
            },
            {
              key: 'smsEditUpdates',
              label: 'SMS — Edit Request Status Updates',
              desc: 'Receive SMS for amendment docket status changes'
            },
            {
              key: 'emailSystemAlerts',
              label: 'Email — System & Security Alerts',
              desc: 'Critical portal alerts, integrity warnings, and system notices'
            }
          ].map(({ key, label, desc }) => (
            <div
              key={key}
              className="flex items-center justify-between gap-4 py-3.5 border-b border-slate-100 dark:border-slate-800 last:border-0"
            >
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">{label}</div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">{desc}</div>
              </div>
              <Toggle
                id={`notif-${key}`}
                checked={notifPrefs[key]}
                onChange={() => toggleNotif(key)}
              />
            </div>
          ))}
        </div>
      </div>

      {/* ── 4. Language & Theme ── */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs">
        <SectionHeader
          icon={Globe}
          title="Language & Theme"
          subtitle="Controls mirror the site-wide toggles in the top strip"
        />
        <div className="space-y-0 max-w-lg">

          {/* Language toggle */}
          <div className="flex items-center justify-between gap-4 py-3.5 border-b border-slate-100 dark:border-slate-800">
            <div>
              <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">Interface Language</div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                Currently: <strong>{lang === 'en' ? 'English' : 'हिन्दी'}</strong>
              </div>
            </div>
            <button
              id="settings-lang-toggle"
              onClick={onToggleLang}
              className={`px-4 py-2 ${accentBtnCls} text-white text-xs font-bold rounded-xl transition-all cursor-pointer flex items-center gap-1.5 shadow-xs whitespace-nowrap`}
            >
              <Globe className="w-3.5 h-3.5" />
              {lang === 'en' ? 'Switch to हिन्दी' : 'Switch to English'}
            </button>
          </div>

          {/* Dark / Light mode toggle */}
          <div className="flex items-center justify-between gap-4 py-3.5">
            <div>
              <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">Display Theme</div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                Currently: <strong>{darkMode ? 'Dark Mode' : 'Light Mode'}</strong>
              </div>
            </div>
            <button
              id="settings-theme-toggle"
              onClick={onToggleDark}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 dark:bg-slate-700 dark:hover:bg-slate-600 text-amber-300 text-xs font-bold rounded-xl transition-all cursor-pointer flex items-center gap-1.5 shadow-xs border border-slate-700 dark:border-slate-600 whitespace-nowrap"
            >
              {darkMode
                ? <><Sun className="w-3.5 h-3.5" />Switch to Light</>
                : <><Moon className="w-3.5 h-3.5" />Switch to Dark</>}
            </button>
          </div>

        </div>
        <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-4">
          Tip: You can also toggle language and dark mode using keyboard shortcuts (Alt+D for dark, Alt+L for language) from anywhere on the portal.
        </p>
      </div>

    </div>
  );
}
