import React from 'react';
import { Copyright, BookOpen, UserCheck } from 'lucide-react';

export default function CopyrightView({ lang = 'en' }) {
  const isHi = lang === 'hi';

  return (
    <div className="flex-1 bg-[#FFF9F2] dark:bg-slate-950 p-4 sm:p-8 flex flex-col items-center select-none min-h-[calc(100vh-140px)] transition-colors">
      <div className="max-w-4xl w-full space-y-8">
        
        {/* Header */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xs text-center">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 mx-auto flex items-center justify-center mb-4">
            <Copyright className="w-6 h-6" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            {isHi ? 'कॉपीराइट नीति' : 'Copyright Policy'}
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
            {isHi 
              ? 'SecureChain DMS पोर्टल सामग्री स्वामित्व।' 
              : 'SecureChain DMS portal content ownership.'}
          </p>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
          
          <div className="flex items-start gap-4">
            <BookOpen className="w-5 h-5 text-indigo-500 mt-0.5 flex-shrink-0" />
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                {isHi ? 'सामग्री का स्वामित्व' : 'Content Ownership'}
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                {isHi
                  ? 'इस पोर्टल पर उपलब्ध सामग्री गृह मंत्रालय (MHA), भारत सरकार के स्वामित्व में है। इस सामग्री का व्यावसायिक उपयोग पूरी तरह से प्रतिबंधित है।'
                  : 'The content featured on this portal is owned by the Ministry of Home Affairs (MHA), Government of India. Commercial use of this content is strictly prohibited.'}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 pt-6 border-t border-slate-100 dark:border-slate-800">
            <UserCheck className="w-5 h-5 text-indigo-500 mt-0.5 flex-shrink-0" />
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                {isHi ? 'प्रजनन (Reproduction) नियम' : 'Reproduction Rules'}
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                {isHi
                  ? 'गैर-व्यावसायिक उपयोग के लिए सामग्री को उचित स्रोत का उल्लेख करते हुए पुनः प्रस्तुत किया जा सकता है। किसी भी तीसरे पक्ष की सामग्री के लिए संबंधित विभागों से पूर्व अनुमति लेना आवश्यक है।'
                  : 'Material may be reproduced for non-commercial purposes, provided the source is prominently acknowledged. Prior permission is required for the reproduction of any third-party content included on the portal.'}
              </p>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
