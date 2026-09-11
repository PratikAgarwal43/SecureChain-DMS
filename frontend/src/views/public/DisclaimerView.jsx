import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';

export default function DisclaimerView({ lang = 'en' }) {
  const isHi = lang === 'hi';

  return (
    <div className="flex-1 bg-[#FFF9F2] dark:bg-slate-950 p-4 sm:p-8 flex flex-col items-center select-none min-h-[calc(100vh-140px)] transition-colors">
      <div className="max-w-4xl w-full space-y-8">
        
        {/* Header */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xs text-center">
          <div className="w-12 h-12 rounded-2xl bg-rose-50 dark:bg-rose-900/30 text-rose-600 mx-auto flex items-center justify-center mb-4">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            {isHi ? 'अस्वीकरण' : 'Disclaimer'}
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
            {isHi 
              ? 'पोर्टल के उपयोग से संबंधित महत्वपूर्ण जानकारी।' 
              : 'Important information regarding the use of this portal.'}
          </p>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
          
          <div className="flex items-start gap-4">
            <Info className="w-5 h-5 text-rose-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                {isHi
                  ? 'यह पोर्टल भारत सरकार के गृह मंत्रालय द्वारा केवल सूचना और आधिकारिक उद्देश्यों के लिए प्रदान किया गया है। यद्यपि हम इस पोर्टल पर जानकारी को अद्यतित और सटीक रखने का हर संभव प्रयास करते हैं, लेकिन गृह मंत्रालय इसके "जैसा है" के आधार पर प्रदान करता है।'
                  : 'This portal is provided "as is" by the Ministry of Home Affairs, Government of India, for informational and official purposes only. While every effort is made to keep the information on this portal accurate and up-to-date, the Ministry makes no warranties or representations of any kind regarding its completeness or accuracy.'}
              </p>
              
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-4 leading-relaxed">
                {isHi
                  ? 'गृह मंत्रालय इस पोर्टल पर मौजूद किसी भी जानकारी में त्रुटियों, चूक या इसके उपयोग से उत्पन्न होने वाले किसी भी प्रत्यक्ष या अप्रत्यक्ष नुकसान के लिए उत्तरदायी नहीं होगा। किसी भी बाहरी लिंक को केवल सुविधा के लिए शामिल किया गया है, और यह उन साइटों का समर्थन नहीं करता है।'
                  : 'The Ministry shall not be liable for any errors, omissions, or any direct/indirect damages arising from the use of this portal. Any external links provided are for convenience only and do not constitute an endorsement of those external websites.'}
              </p>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
