import React, { useState, useEffect, useRef } from 'react';
import {
  Lock,
  ArrowLeft,
  BadgeCheck,
  AlertCircle
} from 'lucide-react';

import PasswordField from '../components/PasswordField';
import { useToast } from '../context/ToastContext';

/**
 * Official Login Page (/login) — Unified Generic Gateway
 *
 * Design rules:
 *  - ONE form, no visible role tabs or role labels.
 *  - Role is auto-detected from the first 3 characters of the Official ID:
 *      POL → Police / Investigating Officer
 *      JUD → Judicial Authority
 *      FOR / FSL → Forensic Expert
 *      AUD → Statutory Auditor (legacy prefix — routed silently, no label shown)
 *  - As soon as a valid prefix is recognised, a secondary context field
 *    (station / court / lab) slides in below the ID field.
 *  - If the prefix is not recognised, one inline error appears — the error
 *    message does NOT reveal which prefixes are valid.
 *  - Citizen login lives in CitizenPortalView, not here.
 */

// Prefix → role config (kept internal, never rendered as user-facing labels)
const PREFIX_MAP = {
  POL: { role: 'POLICE',   secondaryLabel: 'Assigned Station / Division',    secondaryPlaceholder: 'e.g. Special Investigation Division PS, Mandir Marg' },
  JUD: { role: 'JUDICIAL', secondaryLabel: 'Court / Jurisdiction',           secondaryPlaceholder: 'e.g. Patiala House Courts, New Delhi' },
  FOR: { role: 'FORENSIC', secondaryLabel: 'Laboratory / Unit',              secondaryPlaceholder: 'e.g. Central Forensic Science Laboratory (CFSL)' },
  FSL: { role: 'FORENSIC', secondaryLabel: 'Laboratory / Unit',              secondaryPlaceholder: 'e.g. Central Forensic Science Laboratory (CFSL)' },
};

/** Detect role config from the first 3 chars of an ID string. Returns null if unrecognized. */
function detectFromId(id) {
  if (!id || id.trim().length < 3) return null;
  const prefix = id.trim().slice(0, 3).toUpperCase();
  return PREFIX_MAP[prefix] || null;
}

export default function LoginPage({
  onLoginSuccess,
  onCancel,
  // initialRole is kept in the prop signature for backward compat with App.jsx but is intentionally ignored
  initialRole,
  personas = []
}) {
  const toast = useToast();

  // ── Form state ──────────────────────────────────────────────────────────────
  const [officialId, setOfficialId]         = useState('');
  const [password, setPassword]             = useState('');
  const [secondaryField, setSecondaryField] = useState('');

  // Detected role config: null | { role, secondaryLabel, secondaryPlaceholder }
  const [detected, setDetected]             = useState(null);

  // Inline field errors
  const [fieldErrors, setFieldErrors]       = useState({});

  // Auth-level error (wrong credentials)
  const [errorMsg, setErrorMsg]             = useState('');
  const [loading, setLoading]               = useState(false);

  // Debounce timer ref for live prefix detection
  const debounceRef = useRef(null);

  // ── Auto-detect role from ID prefix ─────────────────────────────────────────
  const runDetection = (value) => {
    const config = detectFromId(value);
    setDetected(config);
    if (value.trim().length >= 3) {
      if (config) {
        // Valid prefix — clear any ID error
        setFieldErrors((prev) => ({ ...prev, officialId: '' }));
      } else {
        // Unrecognised prefix — show inline error (deliberately vague)
        setFieldErrors((prev) => ({
          ...prev,
          officialId: 'ID not recognised — check your Official ID and try again.'
        }));
      }
    } else {
      // Too short to determine yet — clear both
      setFieldErrors((prev) => ({ ...prev, officialId: '' }));
    }
    // Reset secondary field when prefix changes
    setSecondaryField('');
  };

  const handleOfficialIdChange = (e) => {
    const value = e.target.value;
    setOfficialId(value);
    setErrorMsg('');

    // Debounce detection by 280ms so it fires while typing but not on every keystroke
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runDetection(value), 280);
  };

  const handleOfficialIdBlur = (e) => {
    clearTimeout(debounceRef.current);
    runDetection(e.target.value);
  };

  // Clean up debounce on unmount
  useEffect(() => () => clearTimeout(debounceRef.current), []);

  // ── Form submission ──────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    // ── Client-side format gate ──────────────────────────────────────────────
    const idTrimmed = officialId.trim();
    const pwTrimmed = password.trim();

    const newErrors = {};
    if (!idTrimmed) {
      newErrors.officialId = 'Official ID is required.';
    } else if (!detected) {
      newErrors.officialId = 'ID not recognised — check your Official ID and try again.';
    }
    if (!pwTrimmed) {
      newErrors.password = 'Password is required.';
    }

    if (Object.keys(newErrors).length > 0) {
      setFieldErrors(newErrors);
      return;
    }

    setLoading(true);

    setTimeout(() => {
      const portalRole = detected.role;

      // 1. Try exact ID match in personas
      let match = personas.find(
        (p) => p.id?.trim().toUpperCase() === idTrimmed.toUpperCase() && p.portalRole === portalRole
      );

      // 2. Fallback: demo password unlocks the first persona of the detected role
      if (!match && pwTrimmed === '123456') {
        match = personas.find((p) => p.portalRole === portalRole) || personas[0];
      }

      if (!match) {
        setErrorMsg('Authentication rejected by credential gateway. Invalid credentials.');
        setLoading(false);
        return;
      }

      // Merge any typed secondary field so ProfileCard displays what the user entered
      const extraData = {};
      if (detected.secondaryLabel && secondaryField.trim()) {
        if (portalRole === 'POLICE')   extraData.policeStation = secondaryField.trim();
        if (portalRole === 'JUDICIAL') extraData.court         = secondaryField.trim();
        if (portalRole === 'FORENSIC') extraData.labUnit       = secondaryField.trim();
      }

      const enrichedUser = { ...match, ...extraData };
      toast.success(`Authenticated successfully as ${enrichedUser.name}`);
      onLoginSuccess(enrichedUser);
      setLoading(false);
    }, 600);
  };

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="flex-1 bg-[#FFF9F2] dark:bg-slate-950 min-h-[calc(100vh-140px)] p-4 sm:p-8 flex flex-col justify-center items-center transition-colors">
      <div className="max-w-md w-full space-y-6">

        {/* Navigation Return */}
        <button
          onClick={onCancel}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400 hover:text-[#FF6A1A] transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Portal Home</span>
        </button>

        {/* Main Login Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-xl p-6 sm:p-10 space-y-6 transition-colors">

          {/* ── Header ── */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800/60 text-[#FF6A1A] mx-auto flex items-center justify-center shadow-xs">
              <Lock className="w-7 h-7" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-serif">
              Official Login
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-sans">
              Secure access gateway for authorised government officials
            </p>
          </div>

          {/* ── Form ── */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>

            {/* Field 1: Official ID */}
            <div className="space-y-1">
              <label
                htmlFor="official-id"
                className="block text-xs font-bold text-slate-700 dark:text-slate-300"
              >
                Official ID
              </label>
              <input
                id="official-id"
                type="text"
                value={officialId}
                onChange={handleOfficialIdChange}
                onBlur={handleOfficialIdBlur}
                placeholder="Enter your Official ID"
                autoComplete="off"
                autoCapitalize="characters"
                spellCheck={false}
                required
                className={`w-full px-3.5 py-2.5 text-xs font-mono font-bold bg-slate-50 dark:bg-slate-900 border rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#FF6A1A] uppercase transition-colors ${
                  fieldErrors.officialId
                    ? 'border-rose-400 dark:border-rose-600'
                    : detected
                    ? 'border-emerald-400 dark:border-emerald-600'
                    : 'border-slate-300 dark:border-slate-700'
                }`}
              />
              {fieldErrors.officialId && (
                <p className="text-[10px] text-rose-600 dark:text-rose-400 mt-0.5 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3 flex-shrink-0" />
                  {fieldErrors.officialId}
                </p>
              )}
            </div>

            {/* Field 2: Secondary context field — revealed only when a valid prefix is detected */}
            {detected && detected.secondaryLabel && (
              <div className="space-y-1 animate-in fade-in slide-in-from-top-1 duration-200">
                <label
                  htmlFor="secondary-field"
                  className="block text-xs font-bold text-slate-700 dark:text-slate-300"
                >
                  {detected.secondaryLabel}
                </label>
                <input
                  id="secondary-field"
                  type="text"
                  value={secondaryField}
                  onChange={(e) => setSecondaryField(e.target.value)}
                  placeholder={detected.secondaryPlaceholder}
                  autoComplete="off"
                  className="w-full px-3.5 py-2.5 text-xs bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#FF6A1A] transition-colors"
                />
              </div>
            )}

            {/* Field 3: Password */}
            <div className="space-y-0.5">
              <PasswordField
                id="official-password"
                name="password"
                label="Password (Demo: 123456)"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setFieldErrors((prev) => ({ ...prev, password: '' }));
                  setErrorMsg('');
                }}
                onBlur={() => {
                  if (!password.trim()) {
                    setFieldErrors((prev) => ({ ...prev, password: 'Password is required.' }));
                  }
                }}
                placeholder="Enter your password"
                required
              />
              {fieldErrors.password && (
                <p className="text-[10px] text-rose-600 dark:text-rose-400 mt-0.5 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3 flex-shrink-0" />
                  {fieldErrors.password}
                </p>
              )}
            </div>

            {/* Auth-level error banner */}
            {errorMsg && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-[#FF6A1A] hover:bg-[#e05910] text-white font-bold text-xs rounded-xl shadow-md hover:shadow-lg transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <BadgeCheck className="w-4 h-4" />
              <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
            </button>

          </form>

          {/* ── Security notice ── */}
          <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
            <p className="text-[10px] text-slate-400 dark:text-slate-500 text-center leading-relaxed">
              Unauthorised access is a criminal offence under the Information Technology Act, 2000.
              All sessions are audited and immutably recorded.
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
