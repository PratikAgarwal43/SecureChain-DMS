import React from 'react';
import { Eye, Languages, Accessibility, MessageSquareWarning } from 'lucide-react';

export default function AccessibilityView({ lang = 'en' }) {
  const isHi = lang === 'hi';

  const features = [
    {
      title: isHi ? 'WCAG अनुपालन' : 'WCAG Alignment',
      icon: <Accessibility className="w-5 h-5" />,
      desc: isHi 
        ? 'हमारा लक्ष्य सभी उपयोगकर्ताओं के लिए एक सुलभ अनुभव प्रदान करना है, जो Web Content Accessibility Guidelines (WCAG) के अनुरूप हो।'
        : 'We are committed to providing an accessible experience for all users, aligning our design and development with the Web Content Accessibility Guidelines (WCAG).'
    },
    {
      title: isHi ? 'पाठ का आकार और उच्च कंट्रास्ट' : 'Text Size & High Contrast',
      icon: <Eye className="w-5 h-5" />,
      desc: isHi
        ? 'दृष्टिबाधित उपयोगकर्ताओं के लिए, टॉप बार में "A- / A / A+" नियंत्रणों का उपयोग करके पाठ का आकार बदला जा सकता है, और डार्क मोड/हाई कंट्रास्ट टॉगल उपलब्ध हैं।'
        : 'For visually impaired users, text size can be adjusted using the "A- / A / A+" controls in the top bar. High contrast and dark mode toggles are also available.'
    },
    {
      title: isHi ? 'द्विभाषी समर्थन' : 'Bilingual Support',
      icon: <Languages className="w-5 h-5" />,
      desc: isHi
        ? 'पूरा पोर्टल अंग्रेजी और हिंदी दोनों भाषाओं में पूरी तरह से उपलब्ध है। आप किसी भी समय शीर्ष पट्टी से भाषा बदल सकते हैं।'
        : 'The entire portal is fully accessible in both English and Hindi. You can switch languages at any time using the language toggle in the top strip.'
    }
  ];

  return (
    <div className="flex-1 bg-[#FFF9F2] dark:bg-slate-950 p-4 sm:p-8 flex flex-col items-center select-none min-h-[calc(100vh-140px)] transition-colors">
      <div className="max-w-4xl w-full space-y-8">
        
        {/* Header */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xs text-center">
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase bg-sky-100 dark:bg-sky-900/30 text-sky-600 border border-sky-200 dark:border-sky-800">
            {isHi ? 'सुलभता' : 'Accessibility'}
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mt-4">
            {isHi ? 'सुलभता विवरण' : 'Accessibility Statement'}
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
            {isHi 
              ? 'SecureChain DMS को सभी नागरिकों और अधिकारियों के लिए सुलभ बनाने के लिए डिज़ाइन किया गया है।' 
              : 'SecureChain DMS is designed to be accessible to all citizens and officials.'}
          </p>
        </div>

        {/* Features */}
        <div className="grid sm:grid-cols-3 gap-6">
          {features.map((feature, idx) => (
            <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs text-center space-y-4">
              <div className="w-12 h-12 rounded-xl bg-sky-50 dark:bg-sky-900/30 text-sky-600 mx-auto flex items-center justify-center">
                {feature.icon}
              </div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                {feature.title}
              </h2>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Reporting Issues */}
        <div className="bg-sky-50 dark:bg-sky-900/20 border border-sky-200 dark:border-sky-800/50 rounded-3xl p-6 flex items-start gap-4">
          <MessageSquareWarning className="w-6 h-6 text-sky-600 dark:text-sky-400 mt-1 flex-shrink-0" />
          <div>
            <h3 className="text-base font-bold text-sky-900 dark:text-sky-400">
              {isHi ? 'सुलभता समस्या की रिपोर्ट करें' : 'Report an Accessibility Issue'}
            </h3>
            <p className="text-sm text-sky-800 dark:text-sky-300 mt-1">
              {isHi
                ? 'यदि आपको इस पोर्टल का उपयोग करने में कोई कठिनाई आती है, तो कृपया हमें accessibility@mha.gov.in पर ईमेल करें।'
                : 'If you encounter any difficulty using this portal, please contact our support team at accessibility@mha.gov.in so we can assist you and improve our services.'}
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
