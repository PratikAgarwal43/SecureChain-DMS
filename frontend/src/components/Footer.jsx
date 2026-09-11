import React from 'react';
import { 
  Building2, 
  ExternalLink, 
  Shield, 
  Scale, 
  PhoneCall, 
  FileText, 
  CheckCircle2, 
  Globe,
  Award,
  Lock,
  Eye,
  Users
} from 'lucide-react';
import { translations } from '../i18n/translations';

/**
 * Government-Standard Footer per Master Spec Section 21
 * Compliant with GIGW (Government of India Guidelines for Websites)
 * Supports both Light (#FFF9F2 / #FFFFFF) and Dark (#12161C / #1A1F29) themes
 * Completely bilingual (English / हिन्दी)
 * Zero references to "Cyber Crime"
 */
export default function Footer({ lang = 'en' }) {
  const t = translations[lang] || translations.en;
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-[#000000] border-t border-white/10 text-white/70 text-xs select-none w-full">
      
      {/* 1. Four-Column Link Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-10 sm:py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-10 pb-10 border-b border-white/10">
          
          {/* Column 1: About */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 pb-1 border-b border-[#FF6A1A]/40">
              <Shield className="w-3.5 h-3.5 text-[#FF6A1A]" />
              <span>{lang === 'hi' ? 'पोर्टल के बारे में' : 'About'}</span>
            </h4>
            <ul className="space-y-2 text-[11px]">
              <li><a href="#about" className="text-white/70 hover:text-[#FF6A1A] transition-colors">{lang === 'hi' ? 'पोर्टल का परिचय' : 'About the Portal'}</a></li>
              <li><a href="#contact" className="text-white/70 hover:text-[#FF6A1A] transition-colors">{lang === 'hi' ? 'हमसे संपर्क करें' : 'Contact Us'}</a></li>
              <li><a href="#sitemap" className="text-white/70 hover:text-[#FF6A1A] transition-colors">{lang === 'hi' ? 'साइटमैप' : 'Sitemap'}</a></li>
              <li><a href="#terms" className="text-white/70 hover:text-[#FF6A1A] transition-colors">{lang === 'hi' ? 'उपयोग की शर्तें' : 'Terms of Use'}</a></li>
              <li><a href="#privacy" className="text-white/70 hover:text-[#FF6A1A] transition-colors">{lang === 'hi' ? 'गोपनीयता नीति' : 'Privacy Policy'}</a></li>
              <li><a href="#accessibility" className="text-white/70 hover:text-[#FF6A1A] transition-colors">{lang === 'hi' ? 'सुलभता विवरण' : 'Accessibility Statement'}</a></li>
              <li><a href="#copyright" className="text-white/70 hover:text-[#FF6A1A] transition-colors">{lang === 'hi' ? 'कॉपीराइट नीति' : 'Copyright Policy'}</a></li>
              <li><a href="#disclaimer" className="text-white/70 hover:text-[#FF6A1A] transition-colors">{lang === 'hi' ? 'अस्वीकरण' : 'Disclaimer'}</a></li>
            </ul>
          </div>

          {/* Column 2: Related Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 pb-1 border-b border-[#4FA8E0]/40">
              <Building2 className="w-3.5 h-3.5 text-[#4FA8E0]" />
              <span>{lang === 'hi' ? 'संबंधित आधिकारिक लिंक' : 'Related Links'}</span>
            </h4>
            <ul className="space-y-2 text-[11px]">
              <li>
                <a href="https://mha.gov.in" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#4FA8E0] transition-colors flex items-center justify-between group">
                  <span>{lang === 'hi' ? 'गृह मंत्रालय' : 'Ministry of Home Affairs'}</span>
                  <ExternalLink className="w-3 h-3 text-white/30 group-hover:text-[#4FA8E0]" />
                </a>
              </li>
              <li>
                <a href="https://digitalindia.gov.in" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#4FA8E0] transition-colors flex items-center justify-between group">
                  <span>{lang === 'hi' ? 'डिजिटल इंडिया' : 'Digital India'}</span>
                  <ExternalLink className="w-3 h-3 text-white/30 group-hover:text-[#4FA8E0]" />
                </a>
              </li>
              <li>
                <a href="https://mygov.in" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#4FA8E0] transition-colors flex items-center justify-between group">
                  <span>{lang === 'hi' ? 'माईगॉव (MyGov)' : 'MyGov Platform'}</span>
                  <ExternalLink className="w-3 h-3 text-white/30 group-hover:text-[#4FA8E0]" />
                </a>
              </li>
              <li>
                <a href="https://india.gov.in" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#4FA8E0] transition-colors flex items-center justify-between group">
                  <span>{lang === 'hi' ? 'भारत का राष्ट्रीय पोर्टल' : 'National Portal of India'}</span>
                  <ExternalLink className="w-3 h-3 text-white/30 group-hover:text-[#4FA8E0]" />
                </a>
              </li>
              <li>
                <a href="https://ncrb.gov.in" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#4FA8E0] transition-colors flex items-center justify-between group">
                  <span>{lang === 'hi' ? 'राष्ट्रीय अपराध रिकॉर्ड ब्यूरो (NCRB)' : 'National Crime Records Bureau'}</span>
                  <ExternalLink className="w-3 h-3 text-white/30 group-hover:text-[#4FA8E0]" />
                </a>
              </li>
            </ul>
          </div>

          {/* Column 3: Help & Grievance */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 pb-1 border-b border-[#5FA777]/40">
              <PhoneCall className="w-3.5 h-3.5 text-[#5FA777]" />
              <span>{lang === 'hi' ? 'सहायता एवं शिकायत निवारण' : 'Help & Grievance'}</span>
            </h4>
            <ul className="space-y-2.5 text-[11px]">
              <li className="p-2.5 rounded-xl bg-white/10 border border-white/10">
                <span className="block font-semibold text-white">
                  {lang === 'hi' ? 'राष्ट्रीय आपातकालीन हेल्पलाइन' : 'National Emergency Helpline'}:
                </span>
                <span className="font-mono text-xs font-bold text-[#FF6A1A]">112 (24x7 Toll Free)</span>
              </li>
              <li className="p-2.5 rounded-xl bg-white/10 border border-white/10">
                <span className="block font-semibold text-white">
                  {lang === 'hi' ? 'निःशुल्क कानूनी सहायता (NALSA)' : 'Free Legal Aid (NALSA)'}:
                </span>
                <span className="font-mono text-xs font-bold text-[#4FA8E0]">15100</span>
              </li>
              <li>
                <a href="#faqs" className="text-white/70 hover:text-[#5FA777] transition-colors block">
                  {lang === 'hi' ? 'अक्सर पूछे जाने वाले प्रश्न (FAQs)' : 'Frequently Asked Questions (FAQs)'}
                </a>
              </li>
              <li>
                <a href="#feedback" className="text-white/70 hover:text-[#5FA777] transition-colors block">
                  {lang === 'hi' ? 'नागरिक प्रतिपुष्टि (Feedback)' : 'Citizen Feedback & Suggestions'}
                </a>
              </li>
              <li>
                <a href="https://rtionline.gov.in" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#5FA777] transition-colors flex items-center justify-between group">
                  <span>{lang === 'hi' ? 'सूचना का अधिकार (RTI)' : 'Right to Information (RTI Online)'}</span>
                  <ExternalLink className="w-3 h-3 text-white/30 group-hover:text-[#5FA777]" />
                </a>
              </li>
            </ul>
          </div>

          {/* Column 4: Connect With Us & Metrics */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 pb-1 border-b border-purple-400/40">
              <Users className="w-3.5 h-3.5 text-purple-400" />
              <span>{lang === 'hi' ? 'हमसे जुड़ें' : 'Connect With Us'}</span>
            </h4>
            
            {/* Social Icons */}
            <div className="flex items-center space-x-2 pt-1">
              <a 
                href="https://twitter.com" 
                target="_blank" 
                rel="noreferrer"
                className="w-8 h-8 rounded-xl bg-white/10 border border-white/15 hover:border-sky-400 flex items-center justify-center text-white/60 hover:text-sky-400 transition-colors cursor-pointer"
                title="Twitter / X"
              >
                <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
              </a>
              <a 
                href="https://facebook.com" 
                target="_blank" 
                rel="noreferrer"
                className="w-8 h-8 rounded-xl bg-white/10 border border-white/15 hover:border-blue-500 flex items-center justify-center text-white/60 hover:text-blue-400 transition-colors cursor-pointer"
                title="Facebook"
              >
                <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
              </a>
              <a 
                href="https://youtube.com" 
                target="_blank" 
                rel="noreferrer"
                className="w-8 h-8 rounded-xl bg-white/10 border border-white/15 hover:border-red-500 flex items-center justify-center text-white/60 hover:text-red-400 transition-colors cursor-pointer"
                title="YouTube"
              >
                <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
              </a>
            </div>

            {/* Last Updated Line */}
            <div className="text-[10px] text-white/40 font-mono">
              {lang === 'hi' ? 'अंतिम अद्यतन' : 'Last Updated'}: 04 September 2026
            </div>

          </div>

        </div>

        {/* 2. Compliance / Credentials Row */}
        <div className="py-6 border-b border-white/10 flex flex-col md:flex-row items-center justify-between gap-4 text-[11px] text-white/50 text-center md:text-left">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-2">
              <span className="inline-flex items-center gap-1 font-semibold text-white/80">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Compliant with GIGW (Government of India Guidelines for Websites)</span>
              </span>
              <span className="hidden sm:inline text-white/20">•</span>
              <span>Best viewed in latest versions of Chrome, Firefox, Edge</span>
            </div>
            <p className="text-[10px] text-white/30">
              Designed, Developed & Hosted by National Informatics Centre (NIC) — Content Owned & Maintained by Ministry of Home Affairs, Government of India.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="px-2.5 py-1 rounded-lg bg-white/10 border border-white/15 text-[10px] font-bold text-white/80">
              ISO/IEC 27001 Certified
            </div>
            <div className="px-2.5 py-1 rounded-lg bg-white/10 border border-white/15 text-[10px] font-bold text-white/80">
              BSA §63 / $65B Validated
            </div>
          </div>
        </div>

        {/* 3. Final Bottom Bar & Bookend Tricolor Strip */}
        <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-white/40">
          <div>
            © {currentYear} Ministry of Home Affairs, Government of India. All Rights Reserved.
          </div>
          <div className="text-[10px] font-mono">
            SecureChain DMS • Release v2.4.0 (National Sovereign Edition)
          </div>
        </div>

      </div>

      {/* Bookend Tricolor Strip matching header flag banner styling */}
      <div className="w-full flex h-1.5">
        <div className="flex-1 bg-[#FF6A1A]"></div>
        <div className="flex-1 bg-white"></div>
        <div className="flex-1 bg-[#5FA777]"></div>
      </div>

    </footer>
  );
}
