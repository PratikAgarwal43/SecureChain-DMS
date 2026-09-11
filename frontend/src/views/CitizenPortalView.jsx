import React, { useState, useEffect } from 'react';
import { 
  UserCheck, 
  Search, 
  Clock, 
  FileText, 
  ShieldCheck, 
  AlertCircle, 
  LogOut, 
  Phone, 
  KeyRound, 
  FolderCheck, 
  ChevronRight, 
  HelpCircle, 
  Building2, 
  Calendar,
  UploadCloud,
  CheckCircle2,
  Lock,
  ArrowLeft,
  Gavel,
  Download,
  FileCheck
} from 'lucide-react';
import { translations } from '../i18n/translations';
import PasswordField from '../components/PasswordField';
import DragDropUploader from '../components/DragDropUploader';
import { Skeleton, SkeletonTable } from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import { useToast } from '../context/ToastContext';
import ProfileCard from '../components/ProfileCard';

export default function CitizenPortalView({ 
  lang = 'en', 
  activeUser,
  onBackToHome 
}) {
  const t = translations[lang] || translations.en;
  const toast = useToast();

  // Authentication State
  const [citizenSession, setCitizenSession] = useState(activeUser || null);
  const [loginTab, setLoginTab] = useState('mobile'); // 'mobile' | 'ack'
  const [mobileNumber, setMobileNumber] = useState('');
  const [ackNumber, setAckNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetchingRecords, setFetchingRecords] = useState(false);
  const [loginError, setLoginError] = useState('');

  // Per-field inline validation errors (additive — loginError banner still exists)
  const [fieldErrors, setFieldErrors] = useState({});

  /** UX-layer format validation for citizen portal fields. */
  const validateField = (name, value) => {
    const v = (value || '').trim();
    switch (name) {
      case 'mobileNumber':
        if (!v) return 'Mobile number is required.';
        if (!/^\d{10}$/.test(v)) return 'Must be exactly 10 digits (numbers only).';
        return '';
      case 'ackNumber':
        if (!v) return 'Acknowledgement / FIR number is required.';
        return '';
      case 'otp':
        if (!v) return 'OTP is required.';
        if (!/^\d{6}$/.test(v)) return 'OTP must be exactly 6 digits.';
        return '';
      default:
        return '';
    }
  };

  const handleFieldBlur = (name, value) => {
    const err = validateField(name, value);
    setFieldErrors((prev) => ({ ...prev, [name]: err }));
  };


  // Records & Detail View
  const [records, setRecords] = useState([]);
  
  // Citizen Direct Drag & Drop Complaint File
  const [showAttachUploader, setShowAttachUploader] = useState(false);
  const [droppedCitizenDoc, setDroppedCitizenDoc] = useState(null);

  // 10-Minute Auto Logout Timer (600 seconds)
  const [secondsRemaining, setSecondsRemaining] = useState(600);

  useEffect(() => {
    let timer;
    if (citizenSession) {
      timer = setInterval(() => {
        setSecondsRemaining((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            handleCitizenLogout();
            toast.warning("Your citizen session has timed out after 10 minutes of inactivity for privacy protection.");
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [citizenSession]);

  const handleSendOtp = () => {
    if (loginTab === 'mobile' && (!mobileNumber || mobileNumber.length < 10)) {
      setLoginError("Please enter a valid 10-digit registered mobile number.");
      return;
    }
    if (loginTab === 'ack' && !ackNumber) {
      setLoginError("Please enter your Acknowledgement or FIR Number.");
      return;
    }
    setLoginError('');
    setOtpSent(true);
    setOtp('123456');
    toast.info("A 6-digit verification code has been dispatched (Demo: 123456)");
  };

  const handleCitizenLogin = async (e) => {
    e.preventDefault();

    // --- Per-field format validation before fetch ---
    const mobileErr = loginTab === 'mobile' ? validateField('mobileNumber', mobileNumber) : '';
    const ackErr = loginTab === 'ack' ? validateField('ackNumber', ackNumber) : '';
    const otpErr = validateField('otp', otp);

    if (mobileErr || ackErr || otpErr) {
      setFieldErrors((prev) => ({
        ...prev,
        ...(mobileErr ? { mobileNumber: mobileErr } : {}),
        ...(ackErr ? { ackNumber: ackErr } : {}),
        ...(otpErr ? { otp: otpErr } : {}),
      }));
      return;
    }
    // --- End format validation ---

    setLoading(true);
    setLoginError('');

    try {
      const res = await fetch('/api/citizen/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mobileNumber: loginTab === 'mobile' ? mobileNumber : undefined,
          ackNumber: loginTab === 'ack' ? ackNumber : undefined,
          otp: otp || '123456'
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Citizen verification failed");

      setCitizenSession(data.citizen);
      setSecondsRemaining(600);
      toast.success(`Welcome, ${data.citizen.name}! Fetching your crime records...`);

      // Fetch linked records
      setFetchingRecords(true);
      const recRes = await fetch(`/api/citizen/my-records?citizenId=${data.citizen.id}`, {
        headers: { 'x-citizen-id': data.citizen.id }
      });
      if (recRes.ok) {
        const recData = await recRes.json();
        setRecords(recData.records || []);
      }
    } catch (err) {
      setLoginError(err.message);
      toast.error(err.message);
    } finally {
      setLoading(false);
      setFetchingRecords(false);
    }
  };

  const handleCitizenLogout = () => {
    setCitizenSession(null);
    setRecords([]);
    setOtpSent(false);
    setOtp('');
    toast.info("Logged out of citizen portal.");
  };

  const handleUploadCitizenEvidence = () => {
    if (!droppedCitizenDoc) return;
    toast.success(`Supporting evidence ${droppedCitizenDoc.name} attached with hash ${droppedCitizenDoc.sha256.substring(0, 16)}...`);
    setDroppedCitizenDoc(null);
    setShowAttachUploader(false);
  };

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins}:${remainingSecs < 10 ? '0' : ''}${remainingSecs}`;
  };

  return (
    <div className="flex-1 bg-[#FFF9F2] dark:bg-slate-950 min-h-[calc(100vh-140px)] p-3 sm:p-8 flex flex-col justify-start transition-colors w-full">
      <div className="max-w-4xl mx-auto w-full space-y-6">
        
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <button
            onClick={onBackToHome}
            className="text-xs font-semibold text-slate-500 dark:text-slate-400 hover:text-[#FF6A1A] flex items-center gap-1.5 cursor-pointer transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Public Home</span>
          </button>

          {citizenSession && (
            <div className="flex items-center gap-3">
              {/* 10-Minute Timeout Countdown Badge */}
              <div className="flex items-center gap-1.5 px-3 py-1 bg-amber-50 dark:bg-amber-950 border border-amber-300 dark:border-amber-800 rounded-full text-[11px] text-amber-800 dark:text-amber-300 font-mono font-semibold">
                <Clock className="w-3.5 h-3.5 text-amber-600 animate-spin" />
                <span>Session Expiry: <strong>{formatTime(secondsRemaining)}</strong></span>
              </div>

              {/* Logout Button */}
              <button
                onClick={handleCitizenLogout}
                className="px-3 py-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-bold rounded-xl transition-colors flex items-center gap-1 cursor-pointer"
              >
                <LogOut className="w-3 h-3" />
                <span>{t.logout}</span>
              </button>
            </div>
          )}
        </div>

        {/* VIEW 1: CITIZEN LOGIN SCREEN (If not authenticated) */}
        {!citizenSession ? (
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl p-6 sm:p-10 max-w-lg mx-auto space-y-6 transition-colors">
            
            {/* Header with Neutral Grey-Blue Emblem */}
            <div className="text-center space-y-2">
              <div className="w-14 h-14 rounded-2xl bg-[#7B93AD]/15 border border-[#7B93AD]/40 text-[#4E6782] dark:text-[#7B93AD] mx-auto flex items-center justify-center shadow-sm">
                <UserCheck className="w-7 h-7" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                {t.citizenLoginTitle}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t.citizenLoginSubtitle}
              </p>
            </div>

            {/* Login Tabs: Mobile vs Acknowledgement */}
            <div className="flex rounded-2xl bg-slate-100 dark:bg-slate-800 p-1 border border-slate-200 dark:border-slate-700 text-xs font-bold">
              <button
                type="button"
                onClick={() => { setLoginTab('mobile'); setLoginError(''); setOtpSent(false); }}
                className={`flex-1 py-2 rounded-xl transition-all cursor-pointer ${
                  loginTab === 'mobile' 
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm' 
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                }`}
              >
                {t.tabMobileNumber}
              </button>
              <button
                type="button"
                onClick={() => { setLoginTab('ack'); setLoginError(''); setOtpSent(false); }}
                className={`flex-1 py-2 rounded-xl transition-all cursor-pointer ${
                  loginTab === 'ack' 
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm' 
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                }`}
              >
                {t.tabAckNumber}
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleCitizenLogin} className="space-y-4">
              
              {loginTab === 'mobile' ? (
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    {t.mobileNumberLabel}
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-2.5 text-xs text-slate-400 font-bold">+91</span>
                    <input
                      type="tel"
                      value={mobileNumber}
                      onChange={(e) => { setMobileNumber(e.target.value); setFieldErrors((p) => ({ ...p, mobileNumber: '' })); }}
                      onBlur={(e) => handleFieldBlur('mobileNumber', e.target.value)}
                      placeholder={t.mobilePlaceholder}
                      className={`w-full pl-12 pr-4 py-2.5 text-xs bg-slate-50 dark:bg-slate-900 border rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#7B93AD] focus:bg-white dark:focus:bg-slate-950 font-medium ${
                        fieldErrors.mobileNumber ? 'border-rose-400 dark:border-rose-600' : 'border-slate-300 dark:border-slate-700'
                      }`}
                      maxLength={10}
                    />
                  </div>
                  {fieldErrors.mobileNumber && (
                    <p className="text-[10px] text-rose-600 dark:text-rose-400 mt-0.5 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3 flex-shrink-0" />
                      {fieldErrors.mobileNumber}
                    </p>
                  )}
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    {t.ackNumberLabel}
                  </label>
                  <input
                    type="text"
                    value={ackNumber}
                    onChange={(e) => { setAckNumber(e.target.value); setFieldErrors((p) => ({ ...p, ackNumber: '' })); }}
                    onBlur={(e) => handleFieldBlur('ackNumber', e.target.value)}
                    placeholder={t.ackPlaceholder}
                    className={`w-full px-4 py-2.5 text-xs bg-slate-50 dark:bg-slate-900 border rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#7B93AD] focus:bg-white dark:focus:bg-slate-950 font-medium ${
                      fieldErrors.ackNumber ? 'border-rose-400 dark:border-rose-600' : 'border-slate-300 dark:border-slate-700'
                    }`}
                  />
                  {fieldErrors.ackNumber && (
                    <p className="text-[10px] text-rose-600 dark:text-rose-400 mt-0.5 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3 flex-shrink-0" />
                      {fieldErrors.ackNumber}
                    </p>
                  )}
                </div>
              )}

              {/* OTP Field with Show/Hide Toggle */}
              {otpSent && (
                <div className="space-y-0.5">
                  <PasswordField
                    id="citizen-otp-auth"
                    name="otp"
                    label="Enter 6-Digit SMS Verification Code"
                    value={otp}
                    onChange={(e) => { setOtp(e.target.value); setFieldErrors((p) => ({ ...p, otp: '' })); }}
                    onBlur={(e) => handleFieldBlur('otp', e.target.value)}
                    placeholder="123456"
                    maxLength={6}
                    required
                  />
                  {fieldErrors.otp && (
                    <p className="text-[10px] text-rose-600 dark:text-rose-400 mt-0.5 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3 flex-shrink-0" />
                      {fieldErrors.otp}
                    </p>
                  )}
                </div>
              )}


              {loginError && (
                <div className="p-3 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs rounded-xl flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{loginError}</span>
                </div>
              )}

              {/* Action Button */}
              {!otpSent ? (
                <button
                  type="button"
                  onClick={handleSendOtp}
                  className="w-full py-2.5 bg-[#7B93AD] hover:bg-[#68819A] text-white font-bold text-xs rounded-xl shadow-md transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  <KeyRound className="w-3.5 h-3.5" />
                  <span>{t.sendOtpBtn}</span>
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-gradient-to-r from-[#FF6A1A] to-[#FF8C42] hover:from-[#e05910] text-white font-bold text-xs rounded-xl shadow-md transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>{loading ? 'Verifying...' : t.verifyAndLoginBtn}</span>
                </button>
              )}

              {/* Demo Notice */}
              <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-[11px] text-center border border-slate-200 dark:border-slate-700">
                {t.demoCitizenNotice}
              </div>

            </form>
          </div>
        ) : (
          /* VIEW 2: CITIZEN MY-RECORDS VIEW */
          <div className="space-y-6">
            
            {/* Profile Card */}
            <ProfileCard
              activeUser={citizenSession}
              role="CITIZEN"
              documents={records}
              lang={lang}
              onGoToSettings={() => {}}
            />

            {/* Welcome Citizen Header */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-4 sm:p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors w-full">
              <div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700">
                  Verified Citizen Session
                </span>
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                  {t.myRecordsHeading}
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {t.myRecordsSubheading}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowAttachUploader(!showAttachUploader)}
                  className="px-4 py-2 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-bold rounded-xl text-xs border border-slate-300 dark:border-slate-700 shadow-xs transition-all flex items-center gap-2 cursor-pointer"
                >
                  <UploadCloud className="w-4 h-4 text-orange-500" />
                  <span>{showAttachUploader ? 'Hide Evidence Uploader' : '+ Lodge Evidence / Complaint'}</span>
                </button>
              </div>
            </div>

            {/* Direct Drag & Drop Supporting Evidence */}
            {showAttachUploader && (
              <div className="bg-white dark:bg-slate-900 border border-orange-300 dark:border-orange-700/60 rounded-3xl p-6 shadow-sm space-y-4 animate-in fade-in slide-in-from-top-2">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                      Attach Supporting Evidence or Add Supplementary Grievance
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Upload incident photos, chat screenshots, bank transfer statements, or handwritten complaints
                    </p>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-orange-50 dark:bg-orange-950 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
                    Direct Citizen Ingestion
                  </span>
                </div>

                <DragDropUploader
                  onFileSelect={setDroppedCitizenDoc}
                  label="Drag & Drop Evidence File, Photo or PDF Grievance"
                  hint="Supports PDF, JPG, PNG, MP4, MP3 up to 50MB with instant SHA-256 integrity seal"
                  roleColor="#FF6A1A"
                />

                {droppedCitizenDoc && (
                  <div className="flex justify-end pt-2">
                    <button
                      onClick={handleUploadCitizenEvidence}
                      className="px-5 py-2.5 bg-gradient-to-r from-[#FF6A1A] to-[#FF8C42] hover:from-[#E85B0E] text-white text-xs font-bold rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Submit Supporting Evidence to Investigating Officer</span>
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* List of Citizen's Cases (Plain Language ONLY) */}
            <div className="space-y-4">
              {fetchingRecords ? (
                <div className="space-y-3">
                  <Skeleton className="h-32 w-full" />
                  <Skeleton className="h-32 w-full" />
                </div>
              ) : records.length === 0 ? (
                <EmptyState
                  title={t.noRecordsFound || 'No Crime Records Found'}
                  description="There are currently no active FIRs or police complaints linked to this mobile number or acknowledgement."
                  actionLabel="Lodge Grievance"
                  onAction={() => setShowAttachUploader(true)}
                />
              ) : (
                records.map((rec) => (
                  <div 
                    key={rec.id}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-orange-300 dark:hover:border-orange-700 rounded-3xl p-6 shadow-sm transition-all space-y-4 group"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                      <div className="flex items-center space-x-2">
                        <span className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono text-xs font-bold text-slate-800 dark:text-slate-200">
                          FIR No: {rec.firNo}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400">
                          ({rec.year})
                        </span>
                      </div>

                      {/* Plain-Language Status Badge */}
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        rec.status?.startsWith('Verdict Delivered') || rec.status?.startsWith('निर्णय सुनाया गया')
                          ? 'bg-sky-50 dark:bg-sky-950 text-[#4FA8E0] dark:text-sky-300 border border-sky-300 dark:border-sky-800'
                          : rec.status === 'Under Investigation' || rec.status === 'जांच जारी है'
                          ? 'bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800'
                          : rec.status === 'Update Pending Review' || rec.status === 'समीक्षा लंबित है'
                          ? 'bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800'
                          : 'bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                      }`}>
                        {rec.status}
                      </span>
                    </div>

                    <div>
                      <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                        {rec.caseTitle}
                      </h3>
                      <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
                        {rec.incidentSummary}
                      </p>
                    </div>

                    {/* CITIZEN VERDICT DELIVERED TIMELINE CARD (NEW FEATURE) */}
                    {rec.verdict && (
                      <div className="p-4 rounded-2xl bg-sky-50/70 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800/80 space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-xl bg-sky-100 dark:bg-sky-900 text-[#4FA8E0] flex items-center justify-center">
                              <Gavel className="w-4 h-4" />
                            </div>
                            <div>
                              <h4 className="text-xs font-bold text-sky-950 dark:text-sky-100">
                                Verdict Delivered — {new Date(rec.verdict.deliveredAt).toLocaleDateString(lang === 'hi' ? 'hi-IN' : 'en-IN', { month: 'short', day: 'numeric', year: 'numeric' })}
                              </h4>
                              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                                Final Court Ruling Issued & Sealed
                              </span>
                            </div>
                          </div>
                          <span className="px-2.5 py-1 rounded-full text-xs font-extrabold bg-sky-100 dark:bg-sky-900 text-[#4FA8E0] border border-sky-300 dark:border-sky-700 self-start sm:self-auto">
                            Disposition: {rec.verdict.disposition}
                          </span>
                        </div>

                        <div className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-sky-100 dark:border-sky-900/60 text-xs text-slate-800 dark:text-slate-200 space-y-1.5 font-sans">
                          <div className="font-bold text-slate-900 dark:text-slate-100">
                            {rec.verdict.verdictTitle}
                          </div>
                          <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed font-serif italic">
                            "{rec.verdict.summary || 'Court order delivered and formally entered into permanent registry.'}"
                          </p>
                          <div className="text-[10px] text-slate-500 dark:text-slate-400 pt-1">
                            Presiding Bench: <strong>{rec.verdict.bench || rec.verdict.presidingCourt}</strong> • Judge: <strong>{rec.verdict.judgeName}</strong>
                          </div>
                        </div>

                        {/* View / Download Option for Citizen */}
                        <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
                          <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                            <FileCheck className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Certified Sealed Judgment Copy ({rec.verdict.fileSize || '1.8 MB'})</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              const element = document.createElement("a");
                              const file = new Blob([
                                `====================================================\n` +
                                `OFFICIAL JUDICIAL VERDICT & FINAL COURT ORDER\n` +
                                `====================================================\n\n` +
                                `Case FIR: ${rec.firNo}\n` +
                                `Docket Title: ${rec.caseTitle}\n` +
                                `Presiding Court: ${rec.verdict.bench || rec.verdict.presidingCourt}\n` +
                                `Presiding Judicial Officer: ${rec.verdict.judgeName} (${rec.verdict.judgeBadge})\n` +
                                `Date of Pronouncement: ${new Date(rec.verdict.deliveredAt).toLocaleString()}\n` +
                                `Operative Disposition: ${rec.verdict.disposition}\n` +
                                `SHA-256 Immutable Ledger Digest: ${rec.verdict.fileSha256}\n\n` +
                                `OPERATIVE COURT RULING SUMMARY:\n` +
                                `----------------------------------------------------\n` +
                                `${rec.verdict.summary || 'Final order pronounced on merits.'}\n` +
                                `----------------------------------------------------\n` +
                                `Notice: This record is immutably sealed on the MHA SecureChain WORM audit ledger.\n`
                              ], { type: 'text/plain;charset=utf-8' });
                              element.href = URL.createObjectURL(file);
                              element.download = `Verdict_${rec.firNo.replace(/[\/\\:]/g, '_')}.txt`;
                              document.body.appendChild(element);
                              element.click();
                              document.body.removeChild(element);
                              toast.success("Certified Court Verdict downloaded successfully.");
                            }}
                            className="px-3.5 py-1.5 bg-[#4FA8E0] hover:bg-[#3B97D1] text-white text-xs font-bold rounded-xl shadow-xs transition-all flex items-center gap-1.5 cursor-pointer"
                          >
                            <Download className="w-3.5 h-3.5" />
                            <span>View & Download Verdict</span>
                          </button>
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs text-slate-600 dark:text-slate-400">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>{t.dateFiled}: <strong className="text-slate-800 dark:text-slate-200">{new Date(rec.dateReported).toLocaleDateString()}</strong></span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Building2 className="w-3.5 h-3.5 text-slate-400" />
                        <span>{t.stationFiled}: <strong className="text-slate-800 dark:text-slate-200">{rec.policeStation}</strong></span>
                      </div>
                      <div className="flex items-center gap-2">
                        <FolderCheck className="w-3.5 h-3.5 text-slate-400" />
                        <span>Category: <strong className="text-slate-800 dark:text-slate-200">{rec.crimeCategory}</strong></span>
                      </div>
                    </div>

                    {/* Official Custody Note */}
                    <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl text-[11px] text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800">
                      <strong>Official Custody Record:</strong> This legal record is protected against silent alterations under Ministry of Home Affairs evidence standards. Any official updates require formal multi-officer verification.
                    </div>

                  </div>
                ))
              )}
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
