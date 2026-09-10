import React, { useState } from 'react';
import { 
  Shield, 
  Scale, 
  Microscope, 
  ArrowRight, 
  Lock, 
  FileCheck2, 
  CheckCircle2, 
  Bell, 
  AlertTriangle,
  FolderArchive,
  Search,
  BookOpen,
  HelpCircle,
  Clock,
  Sparkles,
  UserCheck,
  Building2,
  FileText,
  FileSearch,
  Database,
  Layers,
  ChevronRight,
  TrendingUp,
  Award,
  ExternalLink,
  Landmark,
  FileSpreadsheet,
  BadgeCheck,
  PhoneCall
} from 'lucide-react';
import { translations } from '../i18n/translations';

/**
 * Pure Informational Landing Page per Master Spec Section 3:
 * - Purely informational / educational / marketing
 * - NO per-role login cards or role selector buttons
 * - Single 'Login' button affordance leading to /login
 * - Plain language outcomes, zero internal technical jargon in headlines
 * - Zero references to "Cyber Crime"
 * - Dark mode and full bilingual support
 */
export default function LandingPage({ 
  onOpenRoleLogin,
  onGoToDashboard,
  onGoToCitizen,
  activeUser, 
  metrics,
  lang = 'en'
}) {
  const t = translations[lang] || translations.en;

  const tickerAdvisories = [
    "Government Gazette: Bharatiya Sakshya Adhiniyam (BSA), 2023 Section 63 electronic certification is now mandatory for court exhibits.",
    "National Standard: Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 Section 173 e-FIR records are secured with permanent digital verification.",
    "Integrity Mandate: Amendments to case records require 2-of-3 independent multi-cadre consensus under statutory evidence rules.",
    "Citizen Alert: National Emergency Helpline 112 and Free Legal Aid 15100 are operational 24x7 across all states and union territories."
  ];

  const institutionalWings = [
    {
      title: "Law Enforcement Agency",
      ministry: "Ministry of Home Affairs",
      description: "First Information Reports (CrPC 154 / BNSS 173), seizure memos, and panchnama dockets sealed at inception.",
      tag: "Police / CID / Central Agencies",
      color: "border-orange-200 dark:border-orange-900 bg-orange-50/50 dark:bg-slate-900",
      accent: "text-[#FF6A1A]"
    },
    {
      title: "Judicial Magistrate Court",
      ministry: "Department of Justice",
      description: "Direct court scrutiny, remands, bail records, and Section 65B / BSA Section 63 digital admissibility verification.",
      tag: "District, Sessions & High Courts",
      color: "border-sky-200 dark:border-sky-900 bg-sky-50/50 dark:bg-slate-900",
      accent: "text-sky-600 dark:text-sky-400"
    },
    {
      title: "Forensic Laboratories",
      ministry: "DFSS / CFSL / RFSL",
      description: "Physical exhibit extractions, DNA analysis reports, chemical examinations, and digital evidence custody seals.",
      tag: "Forensic Experts",
      color: "border-emerald-200 dark:border-emerald-900 bg-emerald-50/50 dark:bg-slate-900",
      accent: "text-emerald-600 dark:text-emerald-400"
    },
    {
      title: "Statutory Audit Authority",
      ministry: "Independent Audit Directorate / MHA",
      description: "Permanent write-once ledger oversight, system-wide integrity checks, and emergency override review.",
      tag: "Certified Auditors",
      color: "border-purple-200 dark:border-purple-900 bg-purple-50/50 dark:bg-slate-900",
      accent: "text-purple-600 dark:text-purple-400"
    }
  ];

  const legalActs = [
    {
      code: "BSA §63 / $65B",
      name: "Bharatiya Sakshya Adhiniyam, 2023",
      section: "Section 63 (Admissibility of Electronic Records)",
      detail: "Replaces Section 65B of Indian Evidence Act 1872. Codifies automated digital verification, device provenance, and custodian signatures for direct courtroom presentation."
    },
    {
      code: "BNSS §173",
      name: "Bharatiya Nagarik Suraksha Sanhita, 2023",
      section: "Section 173 (Information in Cognizable Offenses)",
      detail: "Mandates electronic lodging of FIRs and digital case diary recording. Requires tamper-evident registration of evidence dockets."
    },
    {
      code: "IT Act §79A",
      name: "Information Technology Act, 2000",
      section: "Section 79A & Central Examiner Accreditation",
      detail: "Empowers the Central Government to notify accredited examiners of electronic records, ensuring verification tools adhere to rigorous standards."
    },
    {
      code: "DPDP 2023",
      name: "Digital Personal Data Protection Act, 2023",
      section: "Section 7 & 8 (Statutory Sovereign Exemptions)",
      detail: "Preserves victim and witness privacy with pseudonymous review pools while ensuring lawful state processing under statutory safeguards."
    }
  ];

  return (
    <div className="bg-[#FFF9F2] dark:bg-slate-950 text-slate-800 dark:text-slate-100 flex-1 flex flex-col transition-colors">
      
      {/* 1. What's New Ticker Strip */}
      <div className="bg-[#FFF3E6] dark:bg-slate-900/80 border-b border-orange-200/80 dark:border-slate-800 px-4 sm:px-8 py-2 text-xs flex items-center space-x-3 overflow-hidden select-none">
        <div className="flex items-center gap-1.5 font-bold text-[#FF6A1A] uppercase tracking-wider flex-shrink-0 bg-white dark:bg-slate-800 px-2.5 py-1 rounded-md border border-orange-300 dark:border-orange-800/60 shadow-xs">
          <Bell className="w-3.5 h-3.5 animate-bounce" />
          <span>{lang === 'hi' ? 'ताज़ा सूचना' : "Official Gazette"}</span>
        </div>
        <div className="overflow-hidden whitespace-nowrap text-slate-700 dark:text-slate-300 font-medium text-xs">
          <div className="inline-block animate-marquee pl-4">
            {tickerAdvisories.join("   ✦   ")}
          </div>
        </div>
      </div>

      {/* 2. Hero Section with Indian Flag Watermark (Section 22) */}
      <section className="relative px-4 sm:px-8 pt-12 sm:pt-16 pb-14 max-w-7xl mx-auto w-full overflow-hidden">
        {/* Indian Flag Tricolor Watermark — subtle horizontal bands + Ashoka Chakra */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-3xl" aria-hidden="true">
          {/* Saffron band */}
          <div className="absolute inset-x-0 top-0 h-1/3 bg-[#FF9933] opacity-[0.10] dark:opacity-[0.07]" />
          {/* White band */}
          <div className="absolute inset-x-0 top-1/3 h-1/3 bg-white opacity-[0.08] dark:opacity-[0.04]" />
          {/* Green band */}
          <div className="absolute inset-x-0 top-2/3 h-1/3 bg-[#138808] opacity-[0.10] dark:opacity-[0.07]" />
          {/* Ashoka Chakra — centered SVG wheel watermark */}
          <svg
            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[380px] h-[380px] sm:w-[480px] sm:h-[480px] opacity-[0.09] dark:opacity-[0.06] select-none"
            viewBox="0 0 200 200"
            fill="none"
            aria-hidden="true"
          >
            {/* Outer ring */}
            <circle cx="100" cy="100" r="90" stroke="#000080" strokeWidth="4" />
            {/* Inner ring */}
            <circle cx="100" cy="100" r="78" stroke="#000080" strokeWidth="2" />
            {/* Hub */}
            <circle cx="100" cy="100" r="10" fill="#000080" />
            {/* 24 spokes */}
            {Array.from({ length: 24 }).map((_, i) => {
              const angle = (i * 360) / 24;
              const rad = (angle * Math.PI) / 180;
              const x1 = 100 + 10 * Math.cos(rad);
              const y1 = 100 + 10 * Math.sin(rad);
              const x2 = 100 + 78 * Math.cos(rad);
              const y2 = 100 + 78 * Math.sin(rad);
              return (
                <line
                  key={i}
                  x1={x1.toFixed(2)} y1={y1.toFixed(2)}
                  x2={x2.toFixed(2)} y2={y2.toFixed(2)}
                  stroke="#000080"
                  strokeWidth="2"
                />
              );
            })}
          </svg>
        </div>

        <div className="relative text-center max-w-3xl mx-auto space-y-6">
          
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-orange-100 dark:bg-orange-950/60 border border-orange-300 dark:border-orange-800/80 text-[#FF6A1A] text-xs font-bold shadow-xs">
            <Shield className="w-3.5 h-3.5" />
            <span>National Digital Evidence Architecture • Ministry of Home Affairs</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight font-serif">
            Digital Integrity for <br className="hidden sm:inline" />
            <span className="text-[#FF6A1A]">Police Records & Case Evidence</span>
          </h1>

          <p className="text-xs sm:text-sm md:text-base text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl mx-auto font-sans">
            A national platform for managing investigation and legal documents — FIRs, chargesheets, forensic reports, and court exhibits. Built so no single official can alter a legal record without instant notification and multi-officer approval.
          </p>

          {/* SINGLE Unified Login CTA (per Master Spec Section 3) */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-3">
            <button
              onClick={() => onOpenRoleLogin('POLICE')}
              className="w-full sm:w-auto px-8 py-3.5 bg-gradient-to-r from-[#FF6A1A] to-[#FF8C42] hover:from-[#E85B0E] text-white font-bold text-xs sm:text-sm rounded-2xl shadow-lg hover:shadow-orange-500/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2.5 cursor-pointer"
            >
              <Lock className="w-4 h-4" />
              <span>Login to SecureChain DMS</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <a
              href="#how-it-works"
              className="w-full sm:w-auto px-6 py-3.5 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold text-xs sm:text-sm rounded-2xl border border-slate-300 dark:border-slate-700 shadow-sm hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <BookOpen className="w-4 h-4 text-[#4FA8E0]" />
              <span>How It Works</span>
            </a>
          </div>

          <p className="text-[11px] text-slate-500 dark:text-slate-400 pt-1">
            Access is role-authenticated. Citizens verify by mobile/acknowledgement number; officials sign in via departmental credentials.
          </p>

        </div>
      </section>

      {/* 4. Four Institutional Pillars */}
      <section className="px-4 sm:px-8 py-10 max-w-7xl mx-auto w-full space-y-6">
        <div className="text-center space-y-2">
          <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-orange-100 dark:bg-orange-950 text-[#FF6A1A] border border-orange-200 dark:border-orange-800">
            Four Pillars of Justice
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Inter-Agency Judicial & Law Enforcement Collaboration
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            Zero-trust digital chain of custody enabling verified handoffs across Indian statutory agencies.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 pt-2">
          {institutionalWings.map((wing, i) => (
            <div 
              key={i} 
              className={`border rounded-3xl p-6 space-y-3 transition-all duration-200 hover:-translate-y-1 hover:shadow-md ${wing.color}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300">
                  {wing.tag}
                </span>
                <Landmark className={`w-4 h-4 ${wing.accent}`} />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  {wing.title}
                </h3>
                <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                  {wing.ministry}
                </div>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                {wing.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* 5. How It Works Section (id="how-it-works") */}
      <section id="how-it-works" className="px-4 sm:px-8 py-12 bg-white dark:bg-slate-900/60 border-y border-slate-200 dark:border-slate-800 transition-colors">
        <div className="max-w-7xl mx-auto space-y-8">
          
          <div className="text-center space-y-2">
            <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-orange-100 dark:bg-orange-950 text-[#FF6A1A] border border-orange-200 dark:border-orange-800">
              Core Principles
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              How SecureChain DMS Protects Legal Records
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
              Built to fulfill evidentiary mandates under Bharatiya Sakshya Adhiniyam (BSA) and CCTNS Interoperability guidelines.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 pt-2">
            
            {/* Feature 1 */}
            <div className="bg-[#FFF9F2] dark:bg-slate-900 border border-orange-200/70 dark:border-slate-800 rounded-3xl p-6 space-y-4 hover:border-orange-400 transition-colors shadow-xs">
              <div className="w-12 h-12 rounded-2xl bg-orange-100 dark:bg-orange-950 text-[#FF6A1A] flex items-center justify-center shadow-xs">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Pre-Lock OCR Review
                </h3>
                <span className="text-[10px] font-bold text-[#FF6A1A] uppercase tracking-wider">
                  Human-in-the-Loop
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                Scanned documents undergo automated text extraction. Integrity digests are sealed strictly on the human-confirmed text, preventing scanning noise from corrupting legal dockets.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-[#F4F9FD] dark:bg-slate-900 border border-sky-200/70 dark:border-slate-800 rounded-3xl p-6 space-y-4 hover:border-sky-400 transition-colors shadow-xs">
              <div className="w-12 h-12 rounded-2xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center shadow-xs">
                <Layers className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  No-Overwrite Versioning
                </h3>
                <span className="text-[10px] font-bold text-sky-600 uppercase tracking-wider">
                  Permanent Lineage
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                Original FIR dockets remain permanently pristine. Any supplementary charge-sheet or forensic addendum creates a cryptographically linked child version with complete audit lineage.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-[#F4FAF6] dark:bg-slate-900 border border-emerald-200/70 dark:border-slate-800 rounded-3xl p-6 space-y-4 hover:border-emerald-400 transition-colors shadow-xs">
              <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-xs">
                <FileCheck2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Independent Quorum Approvals
                </h3>
                <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">
                  Multi-Officer Consensus
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                Proposed docket modifications require independent approval from peer officers. Automatic conflict-of-interest enforcement strictly bars investigators from approving their own filings.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-[#F8F5FF] dark:bg-slate-900 border border-purple-200/70 dark:border-slate-800 rounded-3xl p-6 space-y-4 hover:border-purple-400 transition-colors shadow-xs">
              <div className="w-12 h-12 rounded-2xl bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 flex items-center justify-center shadow-xs">
                <Scale className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Judicial Cryptographic Verification
                </h3>
                <span className="text-[10px] font-bold text-purple-600 uppercase tracking-wider">
                  Court Admissibility
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                Direct judicial docket scrutiny under Section 63 BSA 2023 and Evidence Act §65B with real-time SHA-256 hash verification against unalterable root ledgers.
              </p>
            </div>

          </div>

        </div>
      </section>

      {/* 6. Statutory Acts & Central Criminal Laws */}
      <section className="px-4 sm:px-8 py-12 max-w-7xl mx-auto w-full space-y-6">
        <div className="text-center space-y-2">
          <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-orange-100 dark:bg-orange-950 text-[#FF6A1A] border border-orange-200 dark:border-orange-800">
            Legislative Compliance
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Statutory Enactments & Criminal Law Reforms
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            Grounded in the new criminal law enactments passed by the Parliament of India.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
          {legalActs.map((act, i) => (
            <div 
              key={i} 
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 space-y-3 shadow-xs hover:border-slate-300 dark:hover:border-slate-700 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-lg bg-orange-50 dark:bg-orange-950 text-[#FF6A1A] font-mono text-xs font-bold border border-orange-200 dark:border-orange-800">
                  {act.code}
                </span>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Parliament of India
                </span>
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  {act.name}
                </h3>
                <div className="text-xs font-semibold text-[#FF6A1A] mt-0.5">
                  {act.section}
                </div>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                {act.detail}
              </p>
            </div>
          ))}
        </div>
      </section>

    </div>
  );
}
