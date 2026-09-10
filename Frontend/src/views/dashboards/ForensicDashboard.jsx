import React, { useState, useEffect } from 'react';
import { 
  Microscope, 
  UploadCloud, 
  FileSearch, 
  CheckCircle2, 
  AlertTriangle, 
  Thermometer, 
  PackageCheck, 
  Lock, 
  Clock, 
  Eye, 
  Hash, 
  Sparkles, 
  Layers, 
  FileText, 
  Tag, 
  ShieldCheck,
  ArrowRight,
  Database,
  Dna,
  Edit3,
  Check,
  ChevronRight,
  FileCheck,
  FileCheck2
} from 'lucide-react';
import { translations } from '../../i18n/translations';
import DragDropUploader from '../../components/DragDropUploader';
import { useToast } from '../../context/ToastContext';
import RoleSettingsPanel from '../../components/RoleSettingsPanel';
import ProfileCard from '../../components/ProfileCard';


export default function ForensicDashboard({ 
  documents = [], 
  metrics, 
  onSelectDocument, 
  onOpenUpload, 
  onOpenQuorum, 
  onNavigateToApprovals,
  activeUser,
  activeTab = 'overview',
  onSelectTab,
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

  const [droppedFile, setDroppedFile] = useState(null);
  const [reportType, setReportType] = useState('FORENSIC'); // 'FORENSIC' | 'DNA'
  
  // OCR Review Step State (Section 13)
  const [inOcrReview, setInOcrReview] = useState(false);
  const [ocrForm, setOcrForm] = useState({
    caseRef: 'FIR-2024-ND-0842',
    reportTitle: 'Forensic Digital Bitstream & Volatile Memory Analysis',
    analysisSummary: 'Extraction of non-volatile NAND flash exhibits reveals unauthorized API call sequence and altered routing ledger.',
    sensitivityTier: 'HIGH',
    keywords: 'NAND Memory, Altered Ledger, Routing Metadata',
    confidenceScore: 98.6
  });

  // Cases awaiting forensic upload
  const [awaitingCases] = useState([
    {
      firNo: 'FIR-2024-ND-0842',
      caseTitle: 'State vs Syndicate Banking Fraud',
      requiredReport: 'Forensic Digital Memory & Ledger Audit',
      policeStation: 'Mandir Marg P.S., New Delhi',
      dateDispatched: '2024-09-01',
      priority: 'HIGH'
    },
    {
      firNo: 'FIR-2024-MH-1920',
      caseTitle: 'Power Grid SCADA Infiltration',
      requiredReport: 'Forensic Bytecode & PLC Firmware Extraction',
      policeStation: 'Cyber & Special Crimes P.S., Mumbai',
      dateDispatched: '2024-09-02',
      priority: 'HIGH'
    },
    {
      firNo: 'FIR-2024-KA-0518',
      caseTitle: 'Voice Synthesizer Extortion Conspiracy',
      requiredReport: 'Acoustic Spectrogram & DNA Forensic Swab Analysis',
      policeStation: 'Vidhana Soudha P.S., Bengaluru',
      dateDispatched: '2024-09-03',
      priority: 'MEDIUM'
    }
  ]);

  // Simulated OCR & Content Analysis Queue
  const [ocrQueue, setOcrQueue] = useState([
    {
      id: "OCR-7721",
      fileName: "Mobile_Device_Encrypted_Database_Extract.bin",
      caseRef: "FIR-2024-ND-0842",
      fileSize: "84.2 MB",
      confidence: "99.4%",
      reportType: "FORENSIC",
      keywordsFound: ["Beneficiary Ledger", "Diverted Accounts", "Routing Metadata"],
      sensitivityTier: "HIGH",
      sha256: "4a2b9918de55c010a394fe77b1029c4e8810aa345b1289de66c10123fa774431",
      status: "ANALYZED_READY"
    },
    {
      id: "OCR-7722",
      fileName: "SCADA_Substation_Bytecode_Capture.raw",
      caseRef: "FIR-2024-MH-1920",
      fileSize: "1.2 GB",
      confidence: "98.1%",
      reportType: "FORENSIC",
      keywordsFound: ["Command Injection", "Telemetry Corrupt", "Memory Bytecode"],
      sensitivityTier: "HIGH",
      sha256: "a094bb7621cde456881900112aa56e789bc10123ef4512399810a9117bce3210",
      status: "ANALYZED_READY"
    },
    {
      id: "OCR-7723",
      fileName: "Biological_Sample_STR_Allele_DNA_Profile.pdf",
      caseRef: "FIR-2024-KA-0518",
      fileSize: "6.4 MB",
      confidence: "99.8%",
      reportType: "DNA",
      keywordsFound: ["Autosomal STR Marker", "Allele Frequency", "CODIS Loci Match"],
      sensitivityTier: "HIGH",
      sha256: "77aa9011de54bc3210aa98bc45ef123490bcae115623cd89aa102345bc678912",
      status: "ANALYZED_READY"
    }
  ]);

  const sampleCustodyList = [
    {
      sampleId: "SAMPLE-EX-01",
      item: "Seized MicroSD 256GB SanDisk (Ex-01)",
      tamperBagSeal: "GOI-SEAL-8841-A",
      storageCondition: "ESD Faraday Safe, Anti-Static, 4°C Cold Storage",
      custodian: "Forensic Officer (Scientific Examiner)",
      hash: "3d5f8a0e889c2b4c...ab45c11",
      status: "SEALED_INTACT"
    },
    {
      sampleId: "SAMPLE-DNA-04",
      item: "Cotton Swab Buccal Epithelial Specimen (DNA Ex-04)",
      tamperBagSeal: "GOI-BIOSEAL-9912-B",
      storageCondition: "Cryo-Storage Freezer Vault, -20°C Locked Container",
      custodian: "Forensic Officer (Principal DNA Analyst)",
      hash: "55e41aa902bc4511...fa774431",
      status: "SEALED_INTACT"
    }
  ];

  const pendingQuorums = documents.filter(d => d.status === 'PENDING_QUORUM');

  const handleConfirmSeal = (item) => {
    toast.success(`Exhibit ${item.fileName} sealed with sensitivity [${item.sensitivityTier}]`);
    setOcrQueue(prev => prev.filter(q => q.id !== item.id));
  };

  const handleFileDropped = (file) => {
    setDroppedFile(file);
    // Automatically open OCR review step
    setOcrForm({
      caseRef: 'FIR-2024-ND-0842',
      reportTitle: reportType === 'DNA' 
        ? `Forensic DNA Profiling & Loci Matching Report — ${file.name}`
        : `Forensic Laboratory Technical Examination — ${file.name}`,
      analysisSummary: `Comprehensive scientific scrutiny of ${file.name} reveals corroborating cryptographic and forensic traces. Verified under ISO/IEC 17025 standards.`,
      sensitivityTier: 'HIGH',
      keywords: reportType === 'DNA' ? 'DNA Markers, Alleles, Forensic Genetic Loci' : 'Bitstream, Memory Dump, Checksum Intact',
      confidenceScore: 99.2
    });
    setInOcrReview(true);
  };

  const handleConfirmOcrAndLock = () => {
    if (!droppedFile) return;
    toast.success(`Human-confirmed ${reportType} report locked! SHA-256 computed on confirmed content.`);
    
    setOcrQueue(prev => [
      {
        id: `OCR-${Math.floor(1000 + Math.random() * 9000)}`,
        fileName: droppedFile.name,
        caseRef: ocrForm.caseRef,
        fileSize: `${(droppedFile.size / (1024 * 1024)).toFixed(2)} MB`,
        confidence: `${ocrForm.confidenceScore}%`,
        reportType: reportType,
        keywordsFound: ocrForm.keywords.split(',').map(k => k.trim()),
        sensitivityTier: ocrForm.sensitivityTier,
        sha256: droppedFile.sha256,
        status: "ANALYZED_READY"
      },
      ...prev
    ]);

    setDroppedFile(null);
    setInOcrReview(false);
    setCurrentTab('ocr');
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 w-full">
      
      {/* Top Banner Card */}
      <div className="bg-white dark:bg-slate-900 border border-emerald-200 dark:border-slate-800 rounded-3xl p-4 sm:p-8 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors w-full">
        <div className="flex items-center space-x-3 sm:space-x-4">
          <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-800 flex items-center justify-center text-[#5FA777] shadow-xs flex-shrink-0">
            <Microscope className="w-6 h-6 sm:w-7 sm:h-7" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                {t.cardForensicTitle}
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-100 dark:bg-emerald-950 text-[#307044] dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                FSL Scientific & DNA Examination Terminal
              </span>
            </div>
            <p className="text-[11px] sm:text-xs text-slate-500 dark:text-slate-400 mt-1">
              Scientific Examiner: <strong className="text-slate-800 dark:text-slate-200">{activeUser?.name || 'Forensic Officer'}</strong> • Unit: <span className="text-[#5FA777] font-semibold">{activeUser?.labUnit || "CFSL New Delhi"}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => { setReportType('FORENSIC'); setCurrentTab('upload'); }}
            className="px-4 py-2.5 bg-[#5FA777] hover:bg-[#4E9365] text-white font-bold rounded-xl text-xs shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Forensic Report</span>
          </button>
          <button
            onClick={() => { setReportType('DNA'); setCurrentTab('upload'); }}
            className="px-4 py-2.5 bg-sky-700 hover:bg-sky-800 text-white font-bold rounded-xl text-xs shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <Dna className="w-4 h-4" />
            <span>Upload DNA Report</span>
          </button>
        </div>
      </div>

      {/* VIEW: OVERVIEW / HOME */}
      {(currentTab === 'overview' || currentTab === 'home') && (
        <div className="space-y-6 animate-in fade-in">

          {/* Profile Card — identity + My Work snapshot */}
          <ProfileCard
            activeUser={activeUser}
            role="FORENSIC"
            documents={documents}
            lang={lang}
            onGoToSettings={() => setCurrentTab('settings')}
          />

          {/* Grid: 3 Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            
            <div 
              onClick={() => setCurrentTab('custody')}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-emerald-300 dark:hover:border-emerald-600 rounded-3xl p-6 shadow-xs hover:shadow-lg hover:-translate-y-1 transition-all duration-200 space-y-2 group cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Exhibits In Custody
                </span>
                <div className="w-8 h-8 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-[#5FA777] flex items-center justify-center group-hover:scale-110 transition-transform">
                  <PackageCheck className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">
                {sampleCustodyList.length}
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Physical hardware & biological samples sealed in anti-static cryo storage
              </p>
            </div>

            <div 
              onClick={() => setCurrentTab('ocr')}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-sky-300 dark:hover:border-sky-600 rounded-3xl p-6 shadow-xs hover:shadow-lg hover:-translate-y-1 transition-all duration-200 space-y-2 group cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  OCR / Analysis Queue
                </span>
                <div className="w-8 h-8 rounded-xl bg-sky-50 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <FileSearch className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">
                {ocrQueue.length}
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Scientific extractions awaiting final human-confirmed seal
              </p>
            </div>

            <div 
              onClick={() => {
                if (onNavigateToApprovals) onNavigateToApprovals();
                else setCurrentTab('reviews');
              }}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-amber-300 dark:hover:border-amber-600 rounded-3xl p-6 shadow-xs hover:shadow-lg hover:-translate-y-1 transition-all duration-200 space-y-2 group cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Quorum Reviews
                </span>
                <div className="w-8 h-8 rounded-xl bg-amber-50 dark:bg-amber-950 text-amber-500 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Clock className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-extrabold text-amber-600">
                {pendingQuorums.length}
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Technical addendums awaiting peer examination consensus
              </p>
            </div>

          </div>

          {/* Quorum Status Widgets */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Needs Your Approval */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-200">
                  <FileCheck2 className="w-5 h-5 text-[#4FA8E0]" />
                  <span>Quorum Status: Needs Your Approval</span>
                </div>
                <button 
                  onClick={() => {
                    if (onNavigateToApprovals) onNavigateToApprovals();
                    else setCurrentTab('reviews');
                  }}
                  className="text-xs text-[#4FA8E0] hover:underline font-bold"
                >
                  View All
                </button>
              </div>
              
              {(() => {
                const approvalDocs = pendingQuorums.filter(d => d.requesterId !== activeUser?.id);
                return approvalDocs.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {approvalDocs.slice(0, 4).map(doc => {
                      const required = doc.quorum?.required || 3;
                      const current = doc.quorum?.current || 0;
                      return (
                        <div key={doc.id} className="p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex flex-col justify-between">
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-bold font-mono text-slate-900 dark:text-white">{doc.firNo}</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-100 dark:bg-sky-950 text-sky-800 dark:text-sky-300">
                              Action Required
                            </span>
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 mb-2 truncate">
                            {doc.caseTitle}
                          </div>
                          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 mb-1">
                            <div 
                              className="bg-[#4FA8E0] h-1.5 rounded-full transition-all" 
                              style={{ width: `${(current / required) * 100}%` }}
                            ></div>
                          </div>
                          <div className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">
                            {current} of {required} approvals received
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-6 text-center border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl bg-slate-50/50 dark:bg-slate-800/30">
                    <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">No pending approvals right now.</p>
                    <p className="text-xs text-slate-500 mt-1">When an edit request requires your vote, it will appear here.</p>
                  </div>
                );
              })()}
            </div>

            {/* Your Requests */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-200">
                  <FileCheck className="w-5 h-5 text-[#FF6A1A]" />
                  <span>Quorum Status: Your Requests</span>
                </div>
                <button 
                  onClick={() => setCurrentTab('my_requests')}
                  className="text-xs text-[#FF6A1A] hover:underline font-bold"
                >
                  View All
                </button>
              </div>
              
              {(() => {
                const requestDocs = pendingQuorums.filter(d => d.requesterId === activeUser?.id);
                return requestDocs.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {requestDocs.slice(0, 4).map(doc => {
                      const required = doc.quorum?.required || 3;
                      const current = doc.quorum?.current || 0;
                      return (
                        <div key={doc.id} className="p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex flex-col justify-between">
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-bold font-mono text-slate-900 dark:text-white">{doc.firNo}</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300">
                              Pending Quorum
                            </span>
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 mb-2 truncate">
                            {doc.caseTitle}
                          </div>
                          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 mb-1">
                            <div 
                              className="bg-[#FF6A1A] h-1.5 rounded-full transition-all" 
                              style={{ width: `${(current / required) * 100}%` }}
                            ></div>
                          </div>
                          <div className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">
                            {current} of {required} approved
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-6 text-center border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl bg-slate-50/50 dark:bg-slate-800/30">
                    <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">You have no active requests.</p>
                    <p className="text-xs text-slate-500 mt-1">When you request edits, their quorum approval progress will appear here.</p>
                  </div>
                );
              })()}
            </div>

          </div>

          {/* Standards Card */}
          <div className="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl space-y-3">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-200">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Scope Limitation (Section 20.4 Protocol)</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              In accordance with statutory role scoping, the Forensic terminal uploads are strictly limited to <strong>Forensic Examination Reports</strong> and <strong>DNA Analysis Reports</strong>. General FIR filing is strictly reserved for the Police cadre. All uploaded artifacts undergo AES-256 encryption at rest and human-confirmed OCR text hashing.
            </p>
          </div>
        </div>
      )}

      {/* VIEW: REPORTS AWAITING UPLOAD */}
      {currentTab === 'awaiting' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Cases Awaiting Scientific / Forensic Upload
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Dockets formally requisitioned by Police IOs for laboratory or DNA corroboration
              </p>
            </div>
            <span className="px-3 py-1 bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 font-bold text-xs rounded-full border border-amber-300 dark:border-amber-800">
              {awaitingCases.length} Pending Requisitions
            </span>
          </div>

          <div className="space-y-4">
            {awaitingCases.map((c) => (
              <div 
                key={c.firNo}
                className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold bg-white dark:bg-slate-900 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100">
                      {c.firNo}
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300">
                      {c.priority} PRIORITY
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{c.caseTitle}</h4>
                  <p className="text-xs text-[#5FA777] font-semibold flex items-center gap-1">
                    <Microscope className="w-3.5 h-3.5" />
                    <span>Requisitioned: {c.requiredReport}</span>
                  </p>
                  <span className="text-[11px] text-slate-400">
                    Station: {c.policeStation} • Requisition Date: {c.dateDispatched}
                  </span>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => {
                      setReportType(c.requiredReport.includes('DNA') ? 'DNA' : 'FORENSIC');
                      setOcrForm(prev => ({ ...prev, caseRef: c.firNo }));
                      setCurrentTab('upload');
                    }}
                    className="px-4 py-2 bg-[#5FA777] hover:bg-[#4E9365] text-white font-bold rounded-xl text-xs transition-all flex items-center gap-1.5 cursor-pointer shadow-xs"
                  >
                    <span>Upload Report For Case</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* VIEW: UPLOAD NEW REPORT (SCOPED EXCLUSIVELY TO FORENSIC & DNA) */}
      {(currentTab === 'upload' || currentTab === 'ingest') && (
        <div className="bg-white dark:bg-slate-900 border border-emerald-300 dark:border-emerald-700/60 rounded-3xl p-6 sm:p-8 shadow-sm space-y-6 animate-in fade-in">
          
          {/* Header & Scoped Type Selection */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 uppercase">
                  Section 20.4 Strict Scoping
                </span>
                <span className="text-xs text-slate-400 font-mono">ISO/IEC 17025 Certified</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1">
                Upload Scanned Report (Forensic & DNA Only)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Drop scanned report or bitstream. System executes OCR and sensitivity classification before locking.
              </p>
            </div>

            {/* Scoped Report Type Selector */}
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-bold">
              <button
                type="button"
                onClick={() => setReportType('FORENSIC')}
                className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                  reportType === 'FORENSIC'
                    ? 'bg-[#5FA777] text-white shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                }`}
              >
                <Microscope className="w-3.5 h-3.5" />
                <span>Forensic Report</span>
              </button>
              <button
                type="button"
                onClick={() => setReportType('DNA')}
                className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                  reportType === 'DNA'
                    ? 'bg-sky-700 text-white shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                }`}
              >
                <Dna className="w-3.5 h-3.5" />
                <span>DNA Report</span>
              </button>
            </div>
          </div>

          {/* STEP A: DROP ZONE (If not in OCR Review) */}
          {!inOcrReview && (
            <div className="space-y-4">
              <DragDropUploader
                onFileSelect={handleFileDropped}
                label={`Drag & Drop Scanned ${reportType === 'DNA' ? 'Forensic DNA Profiling Certificate' : 'Forensic Technical Examination Report'}`}
                hint="Accepted formats: PDF, TIFF, High-Res Scanned Image, E01 Bitstream up to 2GB. Automatically encrypted via AES-256-GCM."
                roleColor="#5FA777"
              />
            </div>
          )}

          {/* STEP B: OCR REVIEW STEP (SECTION 13) */}
          {inOcrReview && droppedFile && (
            <div className="space-y-6 animate-in fade-in">
              <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 rounded-2xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Sparkles className="w-5 h-5 text-[#5FA777]" />
                  <div>
                    <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">
                      OCR Review Step (Section 13 Compliance)
                    </h4>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400">
                      Review extracted text on right against scanned source. Correct any misrecognized characters before locking. SHA-256 will be calculated on human-confirmed text.
                    </p>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-900/60 px-2.5 py-1 rounded-lg">
                  Confidence {ocrForm.confidenceScore}%
                </span>
              </div>

              {/* Side-By-Side: Original Scan Left, Editable Fields Right */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Left: Original Scan Preview */}
                <div className="p-5 rounded-2xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 space-y-3">
                  <div className="flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
                    <span>Original Scanned Exhibit</span>
                    <span className="font-mono text-[10px] text-slate-400">{(droppedFile.size / (1024 * 1024)).toFixed(2)} MB</span>
                  </div>
                  
                  <div className="aspect-[4/3] bg-white dark:bg-slate-900 rounded-xl border border-slate-300 dark:border-slate-700 p-4 flex flex-col items-center justify-center text-center space-y-2 font-serif text-slate-800 dark:text-slate-200">
                    <Microscope className="w-10 h-10 text-[#5FA777]" />
                    <span className="text-xs font-bold">{droppedFile.name}</span>
                    <span className="text-[10px] font-sans text-slate-400">
                      Previewing page 1 of official lab certificate • Watermark GOI-CFSL
                    </span>
                    <div className="text-[11px] font-mono text-slate-500 bg-slate-50 dark:bg-slate-800 px-3 py-1 rounded border border-slate-200 dark:border-slate-700">
                      Pre-calculated SHA-256: {droppedFile.sha256.substring(0, 20)}...
                    </div>
                  </div>
                </div>

                {/* Right: Editable OCR Fields */}
                <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
                  <div className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center justify-between">
                    <span>Editable OCR-Extracted Fields</span>
                    <span className="text-[10px] text-emerald-600 font-bold">Soft-highlight on review fields</span>
                  </div>

                  <div className="space-y-3 text-xs">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                        Linked Case / FIR Number *
                      </label>
                      <input
                        type="text"
                        value={ocrForm.caseRef}
                        onChange={(e) => setOcrForm({ ...ocrForm, caseRef: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl font-mono text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#5FA777]"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                        Official Report Title *
                      </label>
                      <input
                        type="text"
                        value={ocrForm.reportTitle}
                        onChange={(e) => setOcrForm({ ...ocrForm, reportTitle: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#5FA777]"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                        Extracted Findings & Examination Summary *
                      </label>
                      <textarea
                        rows={3}
                        value={ocrForm.analysisSummary}
                        onChange={(e) => setOcrForm({ ...ocrForm, analysisSummary: e.target.value })}
                        className="w-full px-3 py-2 bg-amber-50/40 dark:bg-amber-950/20 border border-amber-300 dark:border-amber-800 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#5FA777]"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                          Auto-Classified Sensitivity
                        </label>
                        <select
                          value={ocrForm.sensitivityTier}
                          onChange={(e) => setOcrForm({ ...ocrForm, sensitivityTier: e.target.value })}
                          className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl font-bold text-rose-700 dark:text-rose-300 focus:outline-none"
                        >
                          <option value="HIGH">HIGH (State Pool • 3-of-5)</option>
                          <option value="MEDIUM">MEDIUM (District Pool • 2-of-3)</option>
                          <option value="LOW">LOW (District Pool • 1 Approver)</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                          Corroboration Keywords
                        </label>
                        <input
                          type="text"
                          value={ocrForm.keywords}
                          onChange={(e) => setOcrForm({ ...ocrForm, keywords: e.target.value })}
                          className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#5FA777]"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <button
                      type="button"
                      onClick={() => setInOcrReview(false)}
                      className="px-4 py-2 text-xs font-bold text-slate-500 hover:bg-slate-100 rounded-xl"
                    >
                      Re-Drop File
                    </button>
                    <button
                      type="button"
                      onClick={handleConfirmOcrAndLock}
                      className="px-5 py-2.5 bg-[#5FA777] hover:bg-[#4E9365] text-white text-xs font-bold rounded-xl shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Confirm & Lock Report</span>
                    </button>
                  </div>
                </div>

              </div>
            </div>
          )}

        </div>
      )}

      {/* VIEW: OCR / ANALYSIS QUEUE */}
      {currentTab === 'ocr' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs space-y-5 animate-in fade-in">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                OCR & Content Analysis Queue
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Automated character recognition with entity extraction & sensitivity tier assignment
              </p>
            </div>
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">
              {ocrQueue.length} In Review
            </span>
          </div>

          <div className="space-y-4">
            {ocrQueue.length === 0 ? (
              <div className="text-center py-10 text-slate-400 text-xs">
                All uploaded extracts have been certified and sealed into the repository.
              </div>
            ) : (
              ocrQueue.map((item) => (
                <div 
                  key={item.id}
                  className="p-5 rounded-2xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 space-y-3 shadow-xs"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-800 dark:text-slate-200 px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        {item.id}
                      </span>
                      <span className="text-xs text-slate-500 font-mono">
                        {item.caseRef}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 dark:bg-sky-950 text-sky-800 dark:text-sky-300">
                        {item.reportType || 'FORENSIC'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800">
                        TIER: {item.sensitivityTier}
                      </span>
                      <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                        Confidence {item.confidence}
                      </span>
                    </div>
                  </div>

                  <div className="font-bold text-sm text-slate-900 dark:text-slate-100">
                    {item.fileName} ({item.fileSize})
                  </div>

                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {item.keywordsFound.map((kw, i) => (
                      <span key={i} className="text-[10px] bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                        #{kw}
                      </span>
                    ))}
                  </div>

                  <div className="pt-2 border-t border-slate-100 dark:border-slate-700 flex flex-wrap items-center justify-between gap-2">
                    <div className="text-[10px] font-mono text-slate-400 truncate max-w-sm">
                      SHA-256: {item.sha256}
                    </div>

                    <button
                      onClick={() => handleConfirmSeal(item)}
                      className="px-4 py-1.5 bg-[#5FA777] hover:bg-[#4E9365] text-white text-xs font-bold rounded-xl transition-all flex items-center gap-1.5 cursor-pointer shadow-xs"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Confirm & Lock Exhibit</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* VIEW: PHYSICAL & DIGITAL CUSTODY SAFE */}
      {currentTab === 'custody' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs space-y-5 animate-in fade-in">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Physical & Digital Evidence Custody Safe
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                ISO/IEC 17025 certified physical sample tracker with tamper-evident serial bag seal anchors
              </p>
            </div>
            <span className="text-xs font-bold text-[#5FA777] bg-emerald-50 dark:bg-emerald-950 px-3 py-1 rounded-full border border-emerald-200 dark:border-emerald-800">
              Storage Active
            </span>
          </div>

          <div className="space-y-4">
            {sampleCustodyList.map((sample) => (
              <div 
                key={sample.sampleId} 
                className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 font-mono text-xs font-bold text-slate-800 dark:text-slate-200">
                      {sample.sampleId}
                    </span>
                    <span className="text-[10px] font-mono font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-950 px-2 py-0.5 rounded">
                      SEAL: {sample.tamperBagSeal}
                    </span>
                  </div>
                  <div className="font-bold text-sm text-slate-900 dark:text-slate-100">
                    {sample.item}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <Thermometer className="w-3.5 h-3.5 text-blue-500" />
                    <span>{sample.storageCondition}</span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Custodian: <strong>{sample.custodian}</strong>
                  </div>
                </div>

                <div className="text-right space-y-2 flex-shrink-0">
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#5FA777]/15 text-[#307044] dark:text-emerald-300 border border-[#5FA777]/40 block text-center">
                    SEAL INTACT
                  </span>
                  <div className="text-[10px] font-mono text-slate-400">
                    Hash: {sample.hash}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* VIEW: MY REQUESTS (QUORUM STATUS) — READ-ONLY REQUESTER VIEW */}
      {currentTab === 'my_requests' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                Requester Scrutiny View
              </span>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mt-1 font-serif">
                My Requests (Quorum Status)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-sans">
                Read-only tracking of your submitted forensic lab amendments and exhibit findings. Requesters cannot approve their own submissions (Rule 4B lock).
              </p>
            </div>
            <span className="px-3 py-1 bg-amber-50 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800 rounded-xl text-xs font-bold font-mono self-start sm:self-auto">
              {pendingQuorums.length} Active Requests
            </span>
          </div>

          <div className="space-y-4">
            {pendingQuorums.map(doc => {
              const session = doc.quorumSession || {
                threshold: 2,
                totalEligible: 3,
                approvalCount: 1,
                poolLabel: doc.jurisdictionalPool || "District Police Review Pool"
              };
              const approvalCount = session.approvalCount || 1;
              const threshold = session.threshold || 2;
              const progressPct = Math.min(100, Math.round((approvalCount / threshold) * 100));

              return (
                <div key={doc.id} className="p-5 rounded-2xl bg-amber-50/30 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/60 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-800 px-2.5 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                        {doc.firNo}
                      </span>
                      <span className="text-xs font-bold text-amber-700 dark:text-amber-300">
                        Draft v{doc.draftVersion || '1.1'}
                      </span>
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                      🔴 Pending Quorum
                    </span>
                  </div>

                  <div className="text-xs text-slate-700 dark:text-slate-300">
                    <div className="font-bold text-slate-900 dark:text-slate-100">{doc.caseTitle}</div>
                    <p className="mt-0.5">{doc.incidentSummary}</p>
                  </div>

                  <div className="space-y-1.5 pt-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-600 dark:text-slate-400">Approval Progress:</span>
                      <span className="font-mono text-[11px]">{approvalCount} of {threshold} approvals received</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-[#5FA777] rounded-full" style={{ width: `${progressPct}%` }} />
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between pt-1 border-t border-amber-200/50 dark:border-amber-900/30">
                    <span>Routing: <strong>{session.poolLabel || doc.jurisdictionalPool || "District Police Review Pool"}</strong></span>
                    <span className="text-amber-700 dark:text-amber-300 font-medium">Read-Only: Requester cannot vote on own submitted findings</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VIEW: QUORUM REVIEWS (ACTIONABLE APPROVAL MODE) */}
      {(currentTab === 'reviews' || currentTab === 'approvals') && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                Technical Review Board
              </span>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mt-1">
                Forensic Peer Quorum Verification
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Supplementary digital extractions requiring peer technical scrutiny before ledger commitment
              </p>
            </div>
            <button
              onClick={() => {
                if (onNavigateToApprovals) onNavigateToApprovals();
              }}
              className="px-4 py-2 bg-[#FF6A1A] hover:bg-[#E85B0E] text-white font-bold rounded-xl text-xs flex items-center gap-1.5 cursor-pointer shadow-xs"
            >
              <span>Open Dedicated Quorum Board (/approvals)</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {pendingQuorums.map(doc => (
              <div key={doc.id} className="p-4 bg-[#FFF9F2] dark:bg-slate-800/60 border border-orange-200 dark:border-slate-700 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-900 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                      {doc.firNo}
                    </span>
                    <span className="text-[10px] font-bold text-[#5FA777]">Draft v{doc.draftVersion || '1.1'}</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-slate-100">{doc.caseTitle}</div>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2">{doc.incidentSummary}</p>
                </div>

                <button
                  onClick={() => {
                    if (onOpenQuorum) onOpenQuorum(doc);
                    else if (onNavigateToApprovals) onNavigateToApprovals();
                  }}
                  className="px-4 py-2 bg-[#5FA777] hover:bg-[#4E9365] text-white font-bold rounded-xl text-xs transition-all flex items-center gap-1.5 flex-shrink-0 cursor-pointer"
                >
                  <span>Peer Technical Review</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* VIEW: SETTINGS */}
      {currentTab === 'settings' && (
        <RoleSettingsPanel
          activeUser={activeUser}
          role="FORENSIC"
          lang={lang}
          darkMode={darkMode}
          onToggleDark={onToggleDark}
          onToggleLang={onToggleLang}
        />
      )}

    </div>
  );
}
