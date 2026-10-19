import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Sprout, Calendar, Layers, HelpCircle, ArrowRight } from 'lucide-react';

const COMMON_CROPS = [
  { id: 'Wheat', label_en: 'Wheat (गेहूं)', label_hi: 'गेहूं (Wheat)' },
  { id: 'Rice', label_en: 'Rice / Paddy (धान)', label_hi: 'धान / चावल (Rice)' },
  { id: 'Sugarcane', label_en: 'Sugarcane (गन्ना)', label_hi: 'गन्ना (Sugarcane)' },
  { id: 'Maize', label_en: 'Maize / Corn (मक्का)', label_hi: 'मक्का (Maize)' },
  { id: 'Cotton', label_en: 'Cotton (कपास)', label_hi: 'कपास (Cotton)' },
  { id: 'Potato', label_en: 'Potato (आलू)', label_hi: 'आलू (Potato)' },
  { id: 'Tomato', label_en: 'Tomato (टमाटर)', label_hi: 'टमाटर (Tomato)' },
  { id: 'Mustard', label_en: 'Mustard (सरसों)', label_hi: 'सरसों (Mustard)' },
  { id: 'Gram', label_en: 'Gram / Chickpea (चना)', label_hi: 'चना (Gram)' },
  { id: 'Soybean', label_en: 'Soybean (सोयाबीन)', label_hi: 'सोयाबीन (Soybean)' },
  { id: 'Onion', label_en: 'Onion (प्याज)', label_hi: 'प्याज (Onion)' },
  { id: 'Other', label_en: 'Other (Specify below)', label_hi: 'अन्य फसल (नीचे लिखें)' },
];

const SEASONS = [
  { id: 'Rabi', key: 'crop.season_rabi', tagKey: 'crop.season_tag_rabi' },
  { id: 'Kharif', key: 'crop.season_kharif', tagKey: 'crop.season_tag_kharif' },
  { id: 'Zaid', key: 'crop.season_zaid', tagKey: 'crop.season_tag_zaid' },
];

const CropForm = ({ onSubmit, loading }) => {
  const { t, language } = useLanguage();
  const [selectedCrop, setSelectedCrop] = useState('Wheat');
  const [customCrop, setCustomCrop] = useState('');
  const [season, setSeason] = useState('Rabi');
  const [soil, setSoil] = useState('');
  const [question, setQuestion] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const finalCrop = selectedCrop === 'Other' ? (customCrop.trim() || 'Any Crop') : selectedCrop;
    onSubmit({
      crop: finalCrop,
      season,
      soil: soil.trim(),
      question: question.trim(),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-3xl p-6 sm:p-8 border border-emerald-100 shadow-sm space-y-6">
      {/* 1. Crop Selection */}
      <div>
        <label className="block text-base sm:text-lg font-extrabold text-stone-900 mb-2 flex items-center gap-2">
          <Sprout className="w-5 h-5 text-emerald-700" />
          <span>{t('crop.crop_label')}</span>
        </label>
        <select
          value={selectedCrop}
          onChange={(e) => setSelectedCrop(e.target.value)}
          className="w-full text-base sm:text-lg font-semibold bg-stone-50 border-2 border-stone-200 focus:border-emerald-600 focus:bg-white rounded-2xl p-3.5 outline-none transition-all cursor-pointer"
        >
          {COMMON_CROPS.map((c) => (
            <option key={c.id} value={c.id}>
              {language === 'hi' ? c.label_hi : c.label_en}
            </option>
          ))}
        </select>

        {selectedCrop === 'Other' && (
          <input
            type="text"
            required
            placeholder={t('crop.other_crop')}
            value={customCrop}
            onChange={(e) => setCustomCrop(e.target.value)}
            className="w-full mt-3 text-base sm:text-lg bg-stone-50 border-2 border-stone-200 focus:border-emerald-600 focus:bg-white rounded-2xl p-3.5 outline-none transition-all"
          />
        )}
      </div>

      {/* 2. Season Buttons */}
      <div>
        <label className="block text-base sm:text-lg font-extrabold text-stone-900 mb-2 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-emerald-700" />
          <span>{t('crop.season_label')}</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {SEASONS.map((s) => {
            const isSelected = season === s.id;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => setSeason(s.id)}
                className={`py-3 px-4 rounded-2xl font-bold text-base border-2 transition-all text-left flex items-center justify-between cursor-pointer ${
                  isSelected
                    ? 'bg-emerald-600 text-white border-emerald-700 shadow-md shadow-emerald-200 scale-[1.02]'
                    : 'bg-stone-50 text-stone-800 border-stone-200 hover:border-emerald-300'
                }`}
              >
                <span>{t(s.tagKey)}</span>
                {isSelected && <span className="text-white text-xs">✔</span>}
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Soil Type (Optional) */}
      <div>
        <label className="block text-base sm:text-lg font-extrabold text-stone-900 mb-2 flex items-center gap-2">
          <Layers className="w-5 h-5 text-emerald-700" />
          <span>{t('crop.soil_label')}</span>
        </label>
        <input
          type="text"
          value={soil}
          onChange={(e) => setSoil(e.target.value)}
          placeholder={t('crop.soil_placeholder')}
          className="w-full text-base sm:text-lg bg-stone-50 border-2 border-stone-200 focus:border-emerald-600 focus:bg-white rounded-2xl p-3.5 outline-none transition-all"
        />
      </div>

      {/* 4. Farmer's Question (Optional) */}
      <div>
        <label className="block text-base sm:text-lg font-extrabold text-stone-900 mb-2 flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-emerald-700" />
          <span>{t('crop.question_label')}</span>
        </label>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={t('crop.question_placeholder')}
          className="w-full text-base sm:text-lg bg-stone-50 border-2 border-stone-200 focus:border-emerald-600 focus:bg-white rounded-2xl p-3.5 outline-none transition-all"
        />
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className="w-full py-4 px-6 rounded-2xl font-extrabold text-lg sm:text-xl text-white bg-emerald-600 hover:bg-emerald-700 active:scale-[0.98] transition-all shadow-lg shadow-emerald-200 flex items-center justify-center gap-3 disabled:opacity-60 cursor-pointer"
      >
        <span>{loading ? t('crop.loading_btn') : t('crop.submit_btn')}</span>
        {!loading && <ArrowRight className="w-6 h-6" />}
      </button>
    </form>
  );
};

export default CropForm;
