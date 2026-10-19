import React from 'react';
import { Loader2 } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

const Loader = ({ message, className = '' }) => {
  const { t } = useLanguage();
  const displayMsg = message || t('common.loading');

  return (
    <div className={`flex flex-col items-center justify-center py-10 px-4 text-center ${className}`}>
      <div className="relative mb-3">
        <div className="w-12 h-12 rounded-full border-4 border-emerald-100 border-t-emerald-600 animate-spin" />
        <span className="absolute inset-0 flex items-center justify-center text-lg select-none">
          🌱
        </span>
      </div>
      <p className="text-stone-700 font-bold text-base sm:text-lg animate-pulse">
        {displayMsg}
      </p>
    </div>
  );
};

export default Loader;
