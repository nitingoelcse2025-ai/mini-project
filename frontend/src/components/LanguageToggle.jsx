import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Globe } from 'lucide-react';

const LanguageToggle = ({ className = '' }) => {
  const { language, toggleLanguage } = useLanguage();

  return (
    <button
      onClick={toggleLanguage}
      type="button"
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full font-bold text-sm tracking-wide transition-all shadow-sm active:scale-95 border ${
        language === 'hi'
          ? 'bg-amber-100 text-amber-900 border-amber-300 hover:bg-amber-200'
          : 'bg-emerald-100 text-emerald-900 border-emerald-300 hover:bg-emerald-200'
      } ${className}`}
      title="Switch Language / भाषा बदलें"
      aria-label="Toggle language between Hindi and English"
    >
      <Globe className="w-4 h-4 text-stone-700" />
      <span>{language === 'hi' ? 'English' : 'हिंदी'}</span>
    </button>
  );
};

export default LanguageToggle;
