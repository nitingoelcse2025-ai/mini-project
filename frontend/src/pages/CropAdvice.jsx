import React, { useState } from 'react';
import apiClient, { getErrorMessage } from '../api/client';
import { useLanguage } from '../context/LanguageContext';
import CropForm from '../components/CropForm';
import Loader from '../components/Loader';
import ErrorMessage from '../components/ErrorMessage';
import { Sprout, Copy, Check, RotateCcw, Share2 } from 'lucide-react';

const formatMarkdown = (text) => {
  if (!text) return null;
  const lines = text.split('\n');

  return lines.map((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) return <div key={idx} className="h-3" />;

    if (trimmed.startsWith('###')) {
      return (
        <h3 key={idx} className="text-xl sm:text-2xl font-black text-emerald-950 mt-4 mb-2">
          {trimmed.replace(/^###\s*/, '')}
        </h3>
      );
    }

    if (trimmed.startsWith('**') && trimmed.endsWith(':**')) {
      return (
        <h4 key={idx} className="text-lg font-extrabold text-emerald-900 mt-3 mb-1">
          {trimmed.slice(2, -3)}:
        </h4>
      );
    }

    if (trimmed.startsWith('•') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const bulletContent = trimmed.replace(/^[•\-\*]\s*/, '');
      return (
        <div key={idx} className="flex items-start gap-2.5 my-1.5 text-base sm:text-lg text-stone-800 leading-relaxed">
          <span className="text-emerald-600 font-bold text-lg select-none">•</span>
          <span>{renderInlineBold(bulletContent)}</span>
        </div>
      );
    }

    return (
      <p key={idx} className="my-1.5 text-base sm:text-lg text-stone-800 leading-relaxed">
        {renderInlineBold(trimmed)}
      </p>
    );
  });
};

const renderInlineBold = (text) => {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-extrabold text-emerald-950">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
};

const CropAdvice = () => {
  const { t, language } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [adviceResult, setAdviceResult] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const handleFetchAdvice = async (formData) => {
    setLoading(true);
    setError('');
    setAdviceResult(null);

    try {
      const response = await apiClient.post('/api/crop-advice', {
        ...formData,
        language,
      });
      setAdviceResult(response.data);
    } catch (err) {
      setError(getErrorMessage(err, t('common.default_error')));
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!adviceResult?.advice) return;
    navigator.clipboard.writeText(adviceResult.advice);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight flex items-center gap-3">
          <span>{t('crop.title')}</span>
        </h1>
        <p className="text-base sm:text-lg text-stone-600 font-medium mt-1">
          {t('crop.subtitle')}
        </p>
      </div>

      {/* Form Card */}
      <CropForm onSubmit={handleFetchAdvice} loading={loading} />

      {/* Loading Indicator */}
      {loading && <Loader message={t('crop.loading_btn')} />}

      {/* Error Banner */}
      <ErrorMessage error={error} onRetry={() => setError('')} />

      {/* Advice Display Card */}
      {adviceResult && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border-2 border-emerald-200 shadow-lg space-y-5 animate-in fade-in duration-300">
          {/* Offline Demo Banner when source is fallback */}
          {adviceResult.source === 'fallback' && (
            <div className="bg-amber-50 border-2 border-amber-300 text-amber-900 rounded-2xl p-4 font-bold text-sm sm:text-base flex items-center gap-2.5 shadow-xs">
              <span className="text-xl">⚠️</span>
              <span>{t('common.offline_demo_banner')}</span>
            </div>
          )}

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-emerald-100 pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-100 px-3 py-1 rounded-full">
                {adviceResult.crop} • {adviceResult.season}
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900 mt-2">
                {t('crop.results_title')}
              </h2>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                type="button"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-stone-100 hover:bg-emerald-50 text-stone-800 hover:text-emerald-800 rounded-xl font-bold text-sm transition-colors border border-stone-200 cursor-pointer"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? t('common.copied') : t('common.copy')}</span>
              </button>
            </div>
          </div>

          {/* Formatted Advice */}
          <div className="prose prose-emerald max-w-none">
            {formatMarkdown(adviceResult.advice)}
          </div>
        </div>
      )}
    </div>
  );
};

export default CropAdvice;
