import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

const ErrorMessage = ({ error, onRetry, className = '' }) => {
  const { t } = useLanguage();
  if (!error) return null;

  return (
    <div
      className={`bg-red-50 border-2 border-red-200 text-red-900 rounded-2xl p-4 sm:p-5 my-4 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${className}`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-bold text-base text-red-900">{t('common.error')}</h4>
          <p className="text-sm sm:text-base text-red-800 font-medium mt-0.5">{error}</p>
        </div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          type="button"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-bold text-sm rounded-xl transition-all shadow-sm active:scale-95"
        >
          <RotateCcw className="w-4 h-4" />
          <span>{t('common.retry')}</span>
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;
