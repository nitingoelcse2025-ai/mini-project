import React, { useState, useEffect } from 'react';
import apiClient, { getErrorMessage } from '../api/client';
import { useLanguage } from '../context/LanguageContext';
import Loader from '../components/Loader';
import ErrorMessage from '../components/ErrorMessage';
import {
  History as HistoryIcon,
  Trash2,
  ChevronDown,
  ChevronUp,
  Sprout,
  CloudSun,
  MessageSquareText,
  ScanEye,
  Calendar,
} from 'lucide-react';

const getTypeIcon = (type) => {
  switch (type) {
    case 'crop':
      return <Sprout className="w-5 h-5 text-emerald-700" />;
    case 'weather':
      return <CloudSun className="w-5 h-5 text-sky-600" />;
    case 'chat':
      return <MessageSquareText className="w-5 h-5 text-amber-600" />;
    case 'plant':
      return <ScanEye className="w-5 h-5 text-teal-600" />;
    default:
      return <HistoryIcon className="w-5 h-5 text-stone-600" />;
  }
};

const getTypeBadgeColor = (type) => {
  switch (type) {
    case 'crop':
      return 'bg-emerald-100 text-emerald-900 border-emerald-200';
    case 'weather':
      return 'bg-sky-100 text-sky-900 border-sky-200';
    case 'chat':
      return 'bg-amber-100 text-amber-900 border-amber-200';
    case 'plant':
      return 'bg-teal-100 text-teal-900 border-teal-200';
    default:
      return 'bg-stone-100 text-stone-800 border-stone-200';
  }
};

const History = () => {
  const { t } = useLanguage();
  const [historyList, setHistoryList] = useState([]);
  const [selectedType, setSelectedType] = useState('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [deletingId, setDeletingId] = useState(null);

  const fetchHistory = async (type = selectedType) => {
    setLoading(true);
    setError('');

    try {
      const response = await apiClient.get('/api/history', {
        params: {
          type,
        },
      });
      setHistoryList(response.data.history || []);
    } catch (err) {
      setError(getErrorMessage(err, t('common.default_error')));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(selectedType);
  }, [selectedType]);

  const toggleExpand = (id) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm(t('history.delete_confirm'))) {
      return;
    }

    setDeletingId(id);
    try {
      await apiClient.delete(`/api/history/${id}`);
      setHistoryList((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setError(getErrorMessage(err, t('common.default_error')));
    } finally {
      setDeletingId(null);
    }
  };

  const filterTabs = [
    { id: 'all', label: t('history.all') },
    { id: 'crop', label: t('history.crop') },
    { id: 'weather', label: t('history.weather') },
    { id: 'chat', label: t('history.chat') },
    { id: 'plant', label: t('history.plant') },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight flex items-center gap-3">
          <span>{t('history.title')}</span>
        </h1>
        <p className="text-base sm:text-lg text-stone-600 font-medium mt-1">
          {t('history.subtitle')}
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-2 pb-2">
        {filterTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedType(tab.id)}
            className={`px-4 py-2.5 rounded-2xl font-bold text-sm sm:text-base transition-all cursor-pointer ${
              selectedType === tab.id
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-200 scale-102'
                : 'bg-white hover:bg-stone-100 text-stone-700 border border-stone-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && <Loader message={t('common.loading')} />}

      {/* Error */}
      <ErrorMessage error={error} onRetry={() => fetchHistory()} />

      {/* History Items List */}
      {!loading && historyList.length === 0 && (
        <div className="bg-white rounded-3xl p-12 text-center border border-stone-200 space-y-3">
          <div className="text-4xl">🌾</div>
          <p className="text-stone-600 font-bold text-lg">{t('history.empty')}</p>
        </div>
      )}

      {!loading && historyList.length > 0 && (
        <div className="space-y-4">
          {historyList.map((item) => {
            const isExpanded = expandedIds.has(item.id);
            return (
              <div
                key={item.id}
                className="bg-white rounded-3xl border border-stone-200 hover:border-emerald-300 shadow-sm transition-all overflow-hidden"
              >
                {/* Header row */}
                <div
                  onClick={() => toggleExpand(item.id)}
                  className="p-5 sm:p-6 flex items-start justify-between gap-4 cursor-pointer hover:bg-stone-50/60 select-none"
                >
                  <div className="flex items-start gap-3.5 flex-1">
                    <div className="p-2.5 rounded-2xl bg-stone-100 flex-shrink-0 mt-0.5">
                      {getTypeIcon(item.type)}
                    </div>

                    <div className="space-y-1 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`text-xs font-bold px-2.5 py-0.5 rounded-full border uppercase ${getTypeBadgeColor(
                            item.type
                          )}`}
                        >
                          {item.type}
                        </span>
                        <span className="text-xs font-medium text-stone-500 flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5" />
                          {new Date(item.created_at).toLocaleString()}
                        </span>
                        <span className="text-xs font-semibold px-2 py-0.2 bg-stone-100 rounded text-stone-600 uppercase">
                          {item.language}
                        </span>
                      </div>

                      <h3 className="font-extrabold text-base sm:text-lg text-stone-900 leading-snug">
                        {item.question}
                      </h3>

                      {!isExpanded && (
                        <p className="text-xs sm:text-sm text-stone-600 line-clamp-2 mt-1 font-medium">
                          {item.response}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
                    <button
                      onClick={(e) => handleDelete(item.id, e)}
                      disabled={deletingId === item.id}
                      type="button"
                      className="p-2 rounded-xl text-stone-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                      title={t('history.delete_btn')}
                      aria-label="Delete query"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>

                    <button
                      type="button"
                      className="p-2 rounded-xl text-stone-500 hover:text-emerald-700 hover:bg-emerald-50 transition-colors"
                      aria-label="Toggle details"
                    >
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-5 sm:px-6 pb-6 pt-2 border-t border-stone-100 bg-stone-50/50">
                    <div className="bg-white rounded-2xl p-4 sm:p-5 border border-stone-200 text-stone-800 text-sm sm:text-base leading-relaxed whitespace-pre-wrap font-medium">
                      {item.response}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default History;
