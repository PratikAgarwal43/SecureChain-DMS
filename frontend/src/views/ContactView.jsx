import React, { useState } from 'react';
import { 
  Building2, 
  Phone, 
  Mail, 
  MapPin, 
  Clock, 
  FileText, 
  ShieldCheck, 
  ExternalLink,
  Send
} from 'lucide-react';
import { translations } from '../i18n/translations';
import { useToast } from '../context/ToastContext';

/**
 * Official Guidelines & Nodal Helpdesk Directory (Light Background)
 */
export default function ContactView({ lang = 'en' }) {
  const t = translations[lang] || translations.en;
  const isHi = lang === 'hi';
  const toast = useToast();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });

  const handleFormSubmit = (e) => {
    e.preventDefault();
    toast.success(
      isHi 
        ? "आपका संदेश सफलतापूर्वक भेज दिया गया है। हमारी टीम जल्द ही आपसे संपर्क करेगी।"
        : "Your message has been sent successfully. Our support team will contact you shortly."
    );
    setFormData({ name: '', email: '', subject: '', message: '' });
  };

  const contacts = [
    {
      unit: "Ministry of Home Affairs (MHA)",
      division: "Investigation & Records Custody Division",
      location: "North Block, Central Secretariat, New Delhi - 110001",
      phone: "011-23092011 / 1930",
      email: "custody-support@mha.gov.in",
      role: "Central Policy & Cryptographic Oversight"
    },
    {
      unit: "Patiala House Courts Special Registry",
      division: "Electronic Evidence Authentication Registry",
      location: "India Gate Circle, New Delhi - 110001",
      phone: "011-23384210",
      email: "registry-phc@delhicourts.nic.in",
      role: "Electronic Evidence Authentication & Admissibility"
    },
    {
      unit: "Central Forensic Science Laboratory (CFSL)",
      division: "Digital & Hardware Evidence Division",
      location: "Block IV, CGO Complex, Lodhi Road, New Delhi - 110003",
      phone: "011-24361280",
      email: "cfsl-evidence@cbi.gov.in",
      role: "Laboratory Examination & Hash Sealing"
    }
  ];

  return (
    <div className="flex-1 bg-[#FFF9F2] dark:bg-slate-950 p-4 sm:p-8 flex flex-col items-center select-none min-h-[calc(100vh-140px)] transition-colors">
      <div className="max-w-5xl w-full space-y-6">
        
        {/* Header */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs">
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-orange-100 dark:bg-orange-900/30 text-[#FF6A1A] border border-orange-200 dark:border-orange-800">
            Official Directory
          </span>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-2">
            {isHi ? 'कानूनी अधिनियम एवं नोडल संपर्क निर्देशिका' : 'Statutory Guidelines & Nodal Authority Directory'}
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Official contact points for electronic evidence verification and custody compliance queries.
          </p>
        </div>

        {/* Contact Form Section */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xs">
          <form onSubmit={handleFormSubmit} className="space-y-4 max-w-2xl mx-auto">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
              {isHi ? 'हमें संदेश भेजें' : 'Send Us a Message'}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  {isHi ? 'नाम' : 'Name'}
                </label>
                <input 
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#FF6A1A]"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  {isHi ? 'ईमेल' : 'Email'}
                </label>
                <input 
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#FF6A1A]"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                {isHi ? 'विषय' : 'Subject'}
              </label>
              <input 
                type="text"
                required
                value={formData.subject}
                onChange={(e) => setFormData({...formData, subject: e.target.value})}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#FF6A1A]"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                {isHi ? 'संदेश' : 'Message'}
              </label>
              <textarea 
                required
                rows={4}
                value={formData.message}
                onChange={(e) => setFormData({...formData, message: e.target.value})}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#FF6A1A] resize-none"
              />
            </div>
            <div className="flex justify-end pt-2">
              <button 
                type="submit"
                className="flex items-center gap-2 px-6 py-2.5 bg-[#FF6A1A] hover:bg-[#E55A0F] text-white text-sm font-bold rounded-xl transition-colors"
              >
                <Send className="w-4 h-4" />
                <span>{isHi ? 'प्रस्तुत करें' : 'Submit'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Directory Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {contacts.map((c, i) => (
            <div key={i} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-xs space-y-3">
              <div className="w-10 h-10 rounded-2xl bg-orange-50 dark:bg-orange-900/30 text-[#FF6A1A] flex items-center justify-center font-bold">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">{c.unit}</h3>
                <span className="text-[10px] text-[#FF6A1A] font-semibold">{c.division}</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">{c.location}</p>
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-1 text-xs text-slate-700 dark:text-slate-300">
                <div>Phone: <strong className="text-slate-900 dark:text-white">{c.phone}</strong></div>
                <div>Email: <strong className="text-slate-900 dark:text-white">{c.email}</strong></div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
