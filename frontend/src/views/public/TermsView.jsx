import React from 'react';
import { FileText, AlertTriangle, Scale, ShieldAlert } from 'lucide-react';

export default function TermsView({ lang = 'en' }) {
  const isHi = lang === 'hi';

  const sections = [
    {
      title: isHi ? '1. स्वीकार्य उपयोग' : '1. Acceptable Use',
      icon: <Scale className="w-5 h-5" />,
      content: isHi
        ? 'इस पोर्टल का उपयोग केवल आधिकारिक सरकारी कार्यों और नागरिकों द्वारा अपने केस को ट्रैक करने के लिए किया जा सकता है। किसी भी अनधिकृत पहुंच या डेटा को बदलने के प्रयास को गंभीरता से लिया जाएगा।'
        : 'This portal is strictly for official government business and authorized citizen tracking. Any unauthorized access, scraping, or attempts to alter immutable records are strictly prohibited.'
    },
    {
      title: isHi ? '2. उपयोगकर्ता की जिम्मेदारियां' : '2. User Responsibilities',
      icon: <AlertTriangle className="w-5 h-5" />,
      content: isHi
        ? 'उपयोगकर्ता सटीक जानकारी प्रदान करने और अपने लॉगिन क्रेडेंशियल (जैसे OTP) को सुरक्षित रखने के लिए जिम्मेदार हैं। अपना क्रेडेंशियल किसी के साथ साझा न करें।'
        : 'Users are responsible for providing accurate information and maintaining the confidentiality of their credentials (including OTPs). Do not share your login details with anyone.'
    },
    {
      title: isHi ? '3. बौद्धिक संपदा' : '3. Intellectual Property Notice',
      icon: <FileText className="w-5 h-5" />,
      content: isHi
        ? 'पोर्टल का सारा कोड, डिज़ाइन और सामग्री गृह मंत्रालय, भारत सरकार की संपत्ति है। अनुमति के बिना इसका व्यावसायिक उपयोग वर्जित है।'
        : 'All code, design, and content on this portal are the intellectual property of the Ministry of Home Affairs, Government of India. Commercial reproduction is strictly prohibited.'
    },
    {
      title: isHi ? '4. कानूनी कार्रवाई' : '4. Legal Action for Misuse',
      icon: <ShieldAlert className="w-5 h-5" />,
      content: isHi
        ? 'सिस्टम का दुरुपयोग (जैसे फर्जी रिकॉर्ड बनाने की कोशिश) सूचना प्रौद्योगिकी अधिनियम, 2000 और अन्य लागू कानूनों के तहत कानूनी कार्रवाई का कारण बन सकता है।'
        : 'Misuse of the system (such as attempting to forge records or bypass security controls) may lead to severe legal action and prosecution under the Information Technology Act, 2000 and other applicable laws.'
    }
  ];

  return (
    <div className="flex-1 bg-[#FFF9F2] dark:bg-slate-950 p-4 sm:p-8 flex flex-col items-center select-none min-h-[calc(100vh-140px)] transition-colors">
      <div className="max-w-4xl w-full space-y-8">
        
        {/* Header */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xs text-center">
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase bg-orange-100 dark:bg-orange-900/30 text-[#FF6A1A] border border-orange-200 dark:border-orange-800">
            {isHi ? 'कानूनी शर्तें' : 'Legal Terms'}
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mt-4">
            {isHi ? 'उपयोग की शर्तें' : 'Terms of Use'}
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
            {isHi 
              ? 'SecureChain DMS का उपयोग करके, आप निम्नलिखित शर्तों से सहमत होते हैं।' 
              : 'By accessing or using SecureChain DMS, you agree to be bound by these terms.'}
          </p>
        </div>

        {/* Content */}
        <div className="space-y-4">
          {sections.map((section, idx) => (
            <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs flex gap-4">
              <div className="flex-shrink-0 mt-1 w-10 h-10 rounded-xl bg-orange-50 dark:bg-orange-900/30 text-[#FF6A1A] flex items-center justify-center">
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
