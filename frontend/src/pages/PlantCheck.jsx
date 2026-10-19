import React, { useState } from 'react';
import apiClient, { getErrorMessage } from '../api/client';
import { useLanguage } from '../context/LanguageContext';
import PlantUpload from '../components/PlantUpload';
import Loader from '../components/Loader';
import ErrorMessage from '../components/ErrorMessage';
import { ScanEye, AlertTriangle, ShieldCheck, Copy, Check } from 'lucide-react';

const formatDiagnosisMarkdown = (text) => {
  if (!text) return null;
  const lines = text.split('\n');

  return lines.map((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) return <div key={idx} className="h-3" />;

    if (trimmed.startsWith('🔍') || trimmed.startsWith('📋') || trimmed.startsWith('💊') || trimmed.startsWith('🛡️')) {
      return (
        <h3 key={idx} className="text-xl sm:text-2xl font-black text-emerald-950 mt-4 mb-2 flex items-center gap-2">
          {renderInlineBold(trimmed)}
        </h3>
      );
    }

    if (trimmed.startsWith('⚠️')) {
      return (
        <div key={idx} className="bg-amber-100/70 border border-amber-300 text-amber-950 rounded-2xl p-4 my-3 font-semibold text-sm sm:text-base">
          {renderInlineBold(trimmed)}
        </div>
      );
    }

    if (trimmed.startsWith('•') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const bulletContent = trimmed.replace(/^[•\-\*]\s*/, '');
      return (
        <div key={idx} className="flex items-start gap-2.5 my-1.5 text-base sm:text-lg text-stone-800 leading-relaxed">
          <span className="text-emerald-700 font-bold select-none">•</span>
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
        <strong key={i} className="font-extrabold text-stone-950">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
};

const PlantCheck = () => {
  const { t, language } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const handleDiagnose = async ({ file, crop }) => {
    setLoading(true);
    setError('');
    setResult(null);

    const formData = new FormData();
    formData.append('image', file);
    formData.append('language', language);
    if (crop) formData.append('crop', crop);

    try {
      const response = await apiClient.post('/api/plant-check', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
    } catch (err) {
      setError(getErrorMessage(err, t('common.default_error')));
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!result?.diagnosis) return;
    navigator.clipboard.writeText(result.diagnosis);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight flex items-center gap-3">
          <span>{t('plant.title')}</span>
        </h1>
        <p className="text-base sm:text-lg text-stone-600 font-medium mt-1">
          {t('plant.subtitle')}
        </p>
      </div>

      {/* Upload Component */}
      <PlantUpload onDiagnose={handleDiagnose} loading={loading} />

      {/* Loading state */}
      {loading && <Loader message={t('plant.analyzing')} />}

      {/* Error state */}
      <ErrorMessage error={error} onRetry={() => setError('')} />

      {/* Diagnosis Report Card */}
      {result && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border-2 border-emerald-200 shadow-xl space-y-5 animate-in fade-in duration-300">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-emerald-100 pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-teal-800 bg-teal-100 px-3 py-1 rounded-full">
                🌿 {result.filename || 'Plant Check'}
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900 mt-2">
                {t('plant.diagnosis_title')}
              </h2>
            </div>

            <button
              onClick={handleCopy}
              type="button"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-stone-100 hover:bg-emerald-50 text-stone-800 hover:text-emerald-800 rounded-xl font-bold text-sm transition-colors border border-stone-200 cursor-pointer"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
              <span>{copied ? t('common.copied') : t('common.copy')}</span>
            </button>
          </div>

          {/* Prominent Safety Disclaimer */}
          <div className="bg-amber-50 border-2 border-amber-300 rounded-2xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-amber-700 shrink-0 mt-0.5" />
            <p className="text-amber-950 font-bold text-sm sm:text-base leading-snug">
              {t('plant.disclaimer')}
            </p>
          </div>

          {/* Formatted Content */}
          <div className="prose prose-emerald max-w-none">
            {formatDiagnosisMarkdown(result.diagnosis)}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlantCheck;
