import React, { useState } from 'react';
import { Copy, Check, AlertTriangle } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

const formatContent = (text) => {
  if (!text) return null;

  // Split lines and render with nice bullet and paragraph spacing
  const lines = text.split('\n');
  return lines.map((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) {
      return <div key={idx} className="h-2" />;
    }

    // Header level 3 ###
    if (trimmed.startsWith('###')) {
      return (
        <h3 key={idx} className="font-extrabold text-base sm:text-lg text-emerald-950 mt-2 mb-1">
          {trimmed.replace(/^###\s*/, '')}
        </h3>
      );
    }

    // Bullet points
    if (trimmed.startsWith('•') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const content = trimmed.replace(/^[•\-\*]\s*/, '');
      return (
        <div key={idx} className="flex items-start gap-2 my-1 text-sm sm:text-base leading-relaxed">
          <span className="text-emerald-700 font-bold select-none">•</span>
          <span>{renderBold(content)}</span>
        </div>
      );
    }

    return (
      <p key={idx} className="my-1 text-sm sm:text-base leading-relaxed">
        {renderBold(trimmed)}
      </p>
    );
  });
};

const renderBold = (str) => {
  // Simple regex for **bold**
  const parts = str.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-bold text-emerald-950">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
};

const ChatBubble = ({ message }) => {
  const { t } = useLanguage();
  const isUser = message.role === 'user';
  const isFallback = message.source === 'fallback';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex gap-3 w-full my-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-10 h-10 rounded-2xl bg-emerald-700 text-white flex items-center justify-center flex-shrink-0 shadow-sm shadow-emerald-200 mt-1 select-none">
          <span className="text-lg">🌾</span>
        </div>
      )}

      <div
        className={`max-w-[85%] sm:max-w-[75%] rounded-3xl p-4 sm:p-5 relative shadow-sm ${
          isUser
            ? 'bg-emerald-600 text-white rounded-tr-sm'
            : 'bg-white border-2 border-emerald-100 text-stone-900 rounded-tl-sm'
        }`}
      >
        {/* Offline Demo Banner when source is fallback */}
        {!isUser && isFallback && (
          <div className="mb-3 px-3 py-1.5 bg-amber-50 border border-amber-300 text-amber-900 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
            <span>{t('common.offline_demo_banner')}</span>
          </div>
        )}

        <div className="flex items-center justify-between gap-3 mb-1.5 pb-1 border-b border-black/5">
          <span
            className={`text-xs font-bold tracking-wide uppercase ${
              isUser ? 'text-emerald-100' : 'text-emerald-800'
            }`}
          >
            {isUser ? t('chat.user_label') : t('chat.assistant_label')}
          </span>
          {!isUser && (
            <button
              onClick={handleCopy}
              type="button"
              className="text-stone-400 hover:text-emerald-700 p-1 rounded-lg hover:bg-stone-100 transition-colors"
              title={t('common.copy_answer')}
              aria-label={t('common.copy_answer')}
            >
              {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
            </button>
          )}
        </div>

        <div className="break-words">
          {isUser ? (
            <p className="text-base sm:text-lg font-medium leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            <div>{formatContent(message.content)}</div>
          )}
        </div>
      </div>

      {isUser && (
        <div className="w-10 h-10 rounded-2xl bg-stone-200 text-stone-700 flex items-center justify-center flex-shrink-0 shadow-sm mt-1 select-none">
          <span className="text-lg">👨‍🌾</span>
        </div>
      )}
    </div>
  );
};

export default ChatBubble;

