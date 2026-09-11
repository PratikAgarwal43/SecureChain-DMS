import React from 'react';
import { Shield, Users, FileText, CheckCircle } from 'lucide-react';

export default function AboutView({ lang = 'en' }) {
  const isHi = lang === 'hi';

  const steps = [
    {
      title: isHi ? 'चरण 1: केस दर्ज करना' : 'Step 1: Case Registration',
      desc: isHi 
        ? 'पुलिस अधिकारी पोर्टल पर केस का विवरण दर्ज करते हैं। दर्ज होने के बाद इसे बदला नहीं जा सकता।'
        : 'Police officers log the case details on the portal. Once logged, the core details are securely locked.'
    },
    {
      title: isHi ? 'चरण 2: सुरक्षित भंडारण' : 'Step 2: Secure Storage',
      desc: isHi
        ? 'सिस्टम डेटा को एक ऐसे डिजिटल वॉल्ट में सुरक्षित करता है जहाँ किसी भी छेड़छाड़ का तुरंत पता चल जाता है।'
        : 'The system protects the data in a digital vault where any unauthorized changes are instantly detected.'
    },
    {
      title: isHi ? 'चरण 3: बहु-अधिकारी अनुमोदन' : 'Step 3: Multi-Officer Approval',
      desc: isHi
        ? 'केस में किसी भी बड़े बदलाव के लिए कई वरिष्ठ अधिकारियों की सहमति आवश्यक होती है।'
        : 'Any major updates to the case require agreement and approval from multiple senior officials.'
    },
    {
      title: isHi ? 'चरण 4: पारदर्शी ट्रैकिंग' : 'Step 4: Transparent Tracking',
      desc: isHi
        ? 'नागरिक किसी भी समय अपने केस की स्थिति देख सकते हैं, जबकि सिस्टम सभी गतिविधियों का सुरक्षित रिकॉर्ड रखता है।'
        : 'Citizens can track their case status anytime, while the system keeps a secure record of all actions.'
    }
  ];

  return (
    <div className="flex-1 bg-[#FFF9F2] dark:bg-slate-950 p-4 sm:p-8 flex flex-col items-center select-none min-h-[calc(100vh-140px)] transition-colors">
      <div className="max-w-5xl w-full space-y-8">
        
        {/* Header */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xs text-center">
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase bg-orange-100 dark:bg-orange-900/30 text-[#FF6A1A] border border-orange-200 dark:border-orange-800">
            {isHi ? 'पोर्टल के बारे में' : 'About the Portal'}
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mt-4">
            SecureChain DMS
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-3 max-w-2xl mx-auto leading-relaxed">
            {isHi
              ? 'यह भारत सरकार के गृह मंत्रालय की एक पहल है, जिसे पुलिस, न्यायपालिका और नागरिकों के बीच डिजिटल साक्ष्यों को सुरक्षित रखने के लिए बनाया गया है।'
              : 'An initiative by the Ministry of Home Affairs, Government of India, designed to secure digital evidence across police, judiciary, and citizens.'}
          </p>
        </div>

        {/* What Problem it Solves & Who it Serves */}
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-sky-50 dark:bg-sky-900/30 text-sky-600 flex items-center justify-center">
              <Shield className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              {isHi ? 'हम क्या समाधान करते हैं' : 'What Problem We Solve'}
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              {isHi
                ? 'सरकारी रिकॉर्ड और डिजिटल साक्ष्यों में बिना किसी निशान के बदलाव (साइलेंट टैंपरिंग) को रोकना। यह सिस्टम सुनिश्चित करता है कि एक बार दर्ज किया गया डेटा सुरक्षित रहे और उस पर पूरा भरोसा किया जा सके।'
                : 'Preventing the silent tampering of government records and digital evidence. This system ensures that once data is logged, it remains secure, verifiable, and completely trustworthy.'}
            </p>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 flex items-center justify-center">
              <Users className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              {isHi ? 'यह किसके लिए है' : 'Who It Serves'}
            </h2>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                {isHi ? 'पुलिस अधिकारी (जांच के लिए)' : 'Police Officials (for investigations)'}
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                {isHi ? 'न्यायिक प्राधिकरण (निर्णय के लिए)' : 'Judicial Authorities (for rulings)'}
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                {isHi ? 'फॉरेंसिक विशेषज्ञ (रिपोर्ट के लिए)' : 'Forensic Experts (for analysis reports)'}
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                {isHi ? 'नागरिक (अपने केस की स्थिति देखने के लिए)' : 'Citizens (to securely track their own cases)'}
              </li>
            </ul>
          </div>
        </div>

        {/* How it Works */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xs space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-orange-50 dark:bg-orange-900/30 text-[#FF6A1A] flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              {isHi ? 'यह कैसे काम करता है' : 'How It Works'}
            </h2>
          </div>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 pt-4">
            {steps.map((step, idx) => (
              <div key={idx} className="space-y-3 relative">
                {/* Visual Connector */}
                {idx !== steps.length - 1 && (
                  <div className="hidden lg:block absolute top-4 left-10 w-[calc(100%-2.5rem)] h-[2px] bg-slate-100 dark:bg-slate-800 z-0"></div>
                )}
                <div className="w-8 h-8 rounded-full bg-[#FF6A1A] text-white flex items-center justify-center font-bold text-sm relative z-10">
                  {idx + 1}
                </div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                  {step.title}
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
