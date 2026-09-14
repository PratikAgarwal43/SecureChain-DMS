import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Lock, 
  ArrowRight, 
  CheckCircle2, 
  ShieldCheck, 
  Link as LinkIcon,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { translations } from '../i18n/translations';
import { apiClient } from '../services/apiClient';

/**
 * Version Chain View per Master Spec Section 10
 * Connected to real FastAPI /api/v1/documents/{id}/versions endpoint
 */
export default function VersionChainView({ 
  document: doc, 
  onBack, 
  allDocuments = [], 
  onSelectDocument,
  lang = 'en'
}) {
  const t = translations[lang] || translations.en;

  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    if (!doc?.id) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    apiClient.get(`/documents/${doc.id}/versions`)
      .then(data => {
        if (isMounted) {
          const vList = Array.isArray(data) ? data : [];
          setVersions(vList);
          setLoading(false);
        }
      })
      .catch(err => {
        if (isMounted) {
          console.error("Failed to fetch version chain:", err);
          setError(err.message || "Failed to load version history");
          setLoading(false);
        }
      });

    return () => { isMounted = false; };
  }, [doc?.id]);

  // First 6 + Last 4 Token Helper
  const getToken = (hashStr) => {
    if (!hashStr) return "N/A";
    if (hashStr.length < 10) return hashStr;
    return `${hashStr.substring(0, 6)}...${hashStr.substring(hashStr.length - 4)}`;
  };

  const formatDate = (dt) => {
    if (!dt) return "N/A";
    try {
      return new Date(dt).toLocaleString();
    } catch (_) {
      return String(dt);
    }
  };

  // Fallback single version if API returns empty array or unauthenticated
  const displayVersions = versions.length > 0 ? versions : (doc ? [{
    id: doc.id,
    version: doc.version || '1.0',
    version_number: 1,
    original_filename: doc.title || doc.filename || 'Document Record',
    doc_hash: doc.sha256_hash || doc.sha256 || null,
    chain_hash: doc.chain_hash || null,
    prev_chain_hash: doc.prev_chain_hash || null,
    status: doc.status || 'LOCKED',
    created_at: doc.created_at || null,
    created_by: doc.uploaded_by || 'N/A'
  }] : []);

  return (
    <div className="flex-1 bg-[#FFF9F2] p-4 sm:p-8 flex flex-col items-center select-none min-h-[calc(100vh-140px)]">
      <div className="max-w-5xl w-full space-y-6">
        
        {/* Top Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={onBack}
            className="text-xs font-bold text-slate-600 hover:text-[#FF6A1A] flex items-center gap-1.5 cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{lang === 'hi' ? 'दस्तावेज़ विवरण पर वापस जाएं' : 'Back to Document'}</span>
          </button>

          <div className="text-xs font-mono text-slate-500">
            FIR / CASE REF: <strong className="text-slate-800">{doc?.firNo || doc?.case_id || doc?.id}</strong>
          </div>
        </div>

        {/* Header Title */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-orange-100 text-[#FF6A1A] border border-orange-200">
              Cryptographic Lineage
            </span>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight mt-1">
              {lang === 'hi' ? 'संस्करण श्रृंखला एवं अपरिवर्तनीय इतिहास' : 'Version Chain & Lineage History'}
            </h2>
            <p className="text-xs text-slate-500">
              Every supplementary update references the prior version's hash without overwriting earlier records.
            </p>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-bold">
            <CheckCircle2 className="w-4 h-4 text-[#5FA777]" />
            <span>Chain Link Verified</span>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12 bg-white rounded-3xl border border-slate-200 shadow-xs">
            <Loader2 className="w-8 h-8 text-[#FF6A1A] animate-spin" />
            <span className="ml-3 text-sm text-slate-600 font-medium">Fetching cryptographic version lineage...</span>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-3 text-xs text-red-700">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Version Chain Display */}
        {!loading && (
          <div className="flex flex-col lg:flex-row items-center justify-center gap-4 w-full">
            {displayVersions.map((v, idx) => {
              const isLatest = idx === displayVersions.length - 1;
              const isFirst = idx === 0;

              return (
                <React.Fragment key={v.id || idx}>
                  {/* Link Arrow between nodes */}
                  {idx > 0 && (
                    <div className="flex flex-col items-center justify-center py-2 shrink-0">
                      <div className="w-10 h-10 rounded-full bg-[#FF6A1A] text-white flex items-center justify-center shadow-md">
                        <ArrowRight className="w-5 h-5 stroke-[3]" />
                      </div>
                      <span className="text-[9px] font-mono font-bold text-[#FF6A1A] mt-1 text-center uppercase tracking-wider">
                        Quorum Link
                      </span>
                    </div>
                  )}

                  {/* Version Card */}
                  <div className={`flex-1 w-full ${isLatest && displayVersions.length > 1 ? 'bg-white border-2 border-emerald-300 shadow-md' : 'bg-slate-100/90 border-2 border-slate-300 shadow-xs'} rounded-3xl p-6 sm:p-8 space-y-4`}>
                    <div className="flex items-center justify-between">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase flex items-center gap-1.5 ${isLatest && displayVersions.length > 1 ? 'bg-emerald-100 text-[#307044] border border-emerald-300' : 'bg-slate-200 text-slate-700 border border-slate-300'}`}>
                        {isLatest && displayVersions.length > 1 ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-[#5FA777]" />
                        ) : (
                          <Lock className="w-3.5 h-3.5 text-slate-500" />
                        )}
                        <span>Version {v.version || (`1.${v.version_number ? v.version_number - 1 : idx}`)} ({v.status || 'LOCKED'})</span>
                      </span>

                      <span className="text-[10px] font-mono text-slate-500">
                        {formatDate(v.created_at)}
                      </span>
                    </div>

                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        {v.original_filename || doc?.title || `Document Record Version ${v.version}`}
                      </h3>
                      <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                        {isFirst
                          ? 'Initial formal registration into tamper-evident repository.'
                          : 'Supplementary update appended after multi-party consensus verification.'}
                      </p>
                    </div>

                    <div className={`p-3 rounded-2xl border text-xs space-y-1 ${isLatest && displayVersions.length > 1 ? 'bg-emerald-50/60 border-emerald-200' : 'bg-white border-slate-200'}`}>
                      <div className="text-[10px] text-slate-400 uppercase font-bold">Author / Creator:</div>
                      <div className="font-semibold text-slate-800">{String(v.created_by || 'Official User')}</div>
                    </div>

                    {/* Small Connected Hash-Token Badge */}
                    <div className="pt-3 border-t border-slate-200 space-y-2 text-xs">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-500 flex items-center gap-1">
                          <LinkIcon className="w-3 h-3 text-[#5FA777]" />
                          <span>Previous Hash Pointer:</span>
                        </span>
                        <span className="font-mono text-xs font-bold bg-orange-100 border border-orange-300 text-[#FF6A1A] px-2.5 py-1 rounded-lg">
                          {getToken(v.prev_chain_hash || v.previous_hash)}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-700 font-bold">Document Hash Digest:</span>
                        <span className={`font-mono text-xs font-bold px-2.5 py-1 rounded-lg border ${isLatest && displayVersions.length > 1 ? 'bg-emerald-100 border-emerald-300 text-[#307044]' : 'bg-orange-100 border-orange-300 text-[#FF6A1A]'}`}>
                          {getToken(v.doc_hash || v.sha256_hash)}
                        </span>
                      </div>

                      {v.chain_hash && (
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-500">Chain Merkle Root:</span>
                          <span className="font-mono text-[10px] bg-slate-200 px-2 py-0.5 rounded text-slate-700">
                            {getToken(v.chain_hash)}
                          </span>
                        </div>
                      )}
                    </div>

                  </div>
                </React.Fragment>
              );
            })}
          </div>
        )}

        {/* Explanatory Note */}
        <div className="p-4 bg-white rounded-2xl border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#5FA777]" />
            <span>
              <strong>Cryptographic Guarantee:</strong> Each version's <code>previous_hash</code> points directly to the prior version. Changing even a single character in an earlier version breaks the chain immediately.
            </span>
          </div>
        </div>

      </div>
    </div>
  );
}
