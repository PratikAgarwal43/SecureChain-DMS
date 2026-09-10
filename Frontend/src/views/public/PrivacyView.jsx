import React from 'react';
import { Database, Lock, Clock, Activity } from 'lucide-react';

export default function PrivacyView({ lang = 'en' }) {
  const isHi = lang === 'hi';

  const sections = [
    {
      title: isHi ? '1. डेटा संग्रह' : '1. Data Collection',
      icon: <Database className="w-5 h-5" />,
      content: isHi
        ? 'हम सत्यापन के लिए आधिकारिक कर्मचारी आईडी, केस डेटा और नागरिक मोबाइल नंबर (OTP के लिए) एकत्र करते हैं।'
        : 'We collect official Employee/Badge IDs for access control, case data for legal records, and citizen mobile numbers strictly for OTP verification.'
    },
    {
      title: isHi ? '2. डेटा का उपयोग और दृश्यता' : '2. Data Usage & Visibility',
      icon: <Lock className="w-5 h-5" />,
      content: isHi
        ? 'नागरिकों का डेटा पूरी तरह से गोपनीय है और इसे केवल संबंधित नागरिक ही देख सकते हैं (Section 6 नियमों के अनुसार)। केस डेटा का उपयोग केवल न्यायिक प्रक्रियाओं के लिए किया जाता है।'
        : 'Citizen data is strictly confidential and is only ever shown to that specific citizen upon successful OTP verification, adhering to Section 6 access rules. Case data is used solely for official judicial and investigative processes.'
    },
    {
      title: isHi ? '3. ऑडिट लॉगिंग' : '3. Comprehensive Audit Logging',
      icon: <Activity className="w-5 h-5" />,
      content: isHi
        ? 'सिस्टम में की गई हर गतिविधि को एक सुरक्षित ऑडिट ट्रेल (WORM) में लॉग किया जाता है। इसे बदला या मिटाया नहीं जा सकता।'
        : 'Every login, view, edit request, and approval is immutably logged in our WORM (Write-Once-Read-Many) audit trail to ensure complete accountability and prevent misuse.'
    },
    {
      title: isHi ? '4. डेटा प्रतिधारण' : '4. Data Retention Policy',
      icon: <Clock className="w-5 h-5" />,
      content: isHi
        ? 'कानूनी आवश्यकताओं (Section 17) के अनुसार, FIR और अदालती फैसलों जैसे सभी डिजिटल रिकॉर्ड सिस्टम में स्थायी रूप से सुरक्षित रखे जाते हैं।'
        : 'In accordance with legal mandates (Section 17 rule), all digital records including FIRs, forensic reports, and judicial verdicts are retained permanently in the secure ledger.'
    }
  ];

  return (
    <div className="flex-1 bg-[#FFF9F2] dark:bg-slate-950 p-4 sm:p-8 flex flex-col items-center select-none min-h-[calc(100vh-140px)] transition-colors">
      <div className="max-w-4xl w-full space-y-8">
        
        {/* Header */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xs text-center">
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 border border-emerald-200 dark:border-emerald-800">
            {isHi ? 'गोपनीयता नीति' : 'Privacy Policy'}
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mt-4">
            {isHi ? 'हम आपके डेटा की सुरक्षा कैसे करते हैं' : 'How We Protect Your Data'}
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
            {isHi 
              ? 'आपकी गोपनीयता और डेटा सुरक्षा हमारी सर्वोच्च प्राथमिकता है।' 
              : 'Your privacy and data security are our highest priorities.'}
          </p>
        </div>

        {/* Content */}
        <div className="grid sm:grid-cols-2 gap-6">
          {sections.map((section, idx) => (
            <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs flex flex-col gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 flex items-center justify-center">
                {section.icon}
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  {section.title}
                </h2>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                  {section.content}
                </p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
