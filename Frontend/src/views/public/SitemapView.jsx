import React from 'react';
import { Map, LayoutGrid, FileText, Lock, Users } from 'lucide-react';

export default function SitemapView({ lang = 'en' }) {
  const isHi = lang === 'hi';

  const sections = [
    {
      title: isHi ? 'सार्वजनिक पृष्ठ' : 'Public Pages',
      icon: <LayoutGrid className="w-5 h-5" />,
      color: 'text-sky-600',
      bg: 'bg-sky-50 dark:bg-sky-900/30',
      links: [
        { name: isHi ? 'होम' : 'Home', href: '#home' },
        { name: isHi ? 'पोर्टल के बारे में' : 'About the Portal', href: '#about' },
        { name: isHi ? 'हमसे संपर्क करें' : 'Contact Us', href: '#contact' },
        { name: isHi ? 'अपने रिकॉर्ड ट्रैक करें' : 'Track My Records', href: '#citizen' }
      ]
    },
    {
      title: isHi ? 'कानूनी और नीतियां' : 'Legal & Policies',
      icon: <FileText className="w-5 h-5" />,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50 dark:bg-emerald-900/30',
      links: [
        { name: isHi ? 'उपयोग की शर्तें' : 'Terms of Use', href: '#terms' },
        { name: isHi ? 'गोपनीयता नीति' : 'Privacy Policy', href: '#privacy' },
        { name: isHi ? 'सुलभता विवरण' : 'Accessibility Statement', href: '#accessibility' },
        { name: isHi ? 'कॉपीराइट नीति' : 'Copyright Policy', href: '#copyright' },
        { name: isHi ? 'अस्वीकरण' : 'Disclaimer', href: '#disclaimer' }
      ]
    },
    {
      title: isHi ? 'अधिकृत पहुंच' : 'Authorized Access',
      icon: <Lock className="w-5 h-5" />,
      color: 'text-[#FF6A1A]',
      bg: 'bg-orange-50 dark:bg-orange-900/30',
      links: [
        { name: isHi ? 'आधिकारिक लॉगिन' : 'Official Login', href: '#login' }
      ]
    }
  ];

  return (
    <div className="flex-1 bg-[#FFF9F2] dark:bg-slate-950 p-4 sm:p-8 flex flex-col items-center select-none min-h-[calc(100vh-140px)] transition-colors">
      <div className="max-w-4xl w-full space-y-8">
        
        {/* Header */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xs text-center">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 mx-auto flex items-center justify-center mb-4">
            <Map className="w-6 h-6" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            {isHi ? 'साइटमैप' : 'Sitemap'}
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
            {isHi 
              ? 'SecureChain DMS पोर्टल के सभी सार्वजनिक पृष्ठों की सूची।' 
              : 'Directory of all public pages on the SecureChain DMS portal.'}
          </p>
        </div>

        {/* Note about authenticated areas */}
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50 rounded-2xl p-4 flex items-start gap-3">
          <Lock className="w-5 h-5 text-amber-600 dark:text-amber-500 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-amber-800 dark:text-amber-400">
              {isHi ? 'प्रतिबंधित क्षेत्र' : 'Restricted Areas'}
            </h3>
            <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
              {isHi
                ? 'विशिष्ट भूमिका-आधारित डैशबोर्ड (जैसे पुलिस, न्यायपालिका, फॉरेंसिक) और केस विवरण केवल आधिकारिक लॉगिन के बाद ही उपलब्ध हैं।'
                : 'Role-specific dashboards (Police, Judicial, Forensic) and case details are only accessible after successful official authentication.'}
            </p>
          </div>
        </div>

        {/* Sitemap Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {sections.map((section, idx) => (
            <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs">
              <div className="flex items-center gap-3 mb-4 pb-4 border-b border-slate-100 dark:border-slate-800">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${section.bg} ${section.color}`}>
                  {section.icon}
                </div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                  {section.title}
                </h2>
              </div>
              <ul className="space-y-3">
                {section.links.map((link, lIdx) => (
                  <li key={lIdx}>
                    <a 
                      href={link.href} 
                      className="text-sm text-slate-600 dark:text-slate-400 hover:text-[#FF6A1A] dark:hover:text-[#FF6A1A] transition-colors"
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
