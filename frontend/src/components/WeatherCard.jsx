import React from 'react';
import {
  Sun,
  Cloud,
  CloudSun,
  CloudRain,
  CloudLightning,
  Droplets,
  Wind,
  Compass,
  Sparkles,
  AlertTriangle,
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

const getWeatherIcon = (iconName) => {
  switch (iconName) {
    case 'sunny':
      return <Sun className="w-10 h-10 sm:w-14 sm:h-14 text-amber-500 animate-pulse-subtle" />;
    case 'partly-cloudy':
      return <CloudSun className="w-10 h-10 sm:w-14 sm:h-14 text-amber-500" />;
    case 'cloudy':
      return <Cloud className="w-10 h-10 sm:w-14 sm:h-14 text-slate-500" />;
    case 'rain':
    case 'heavy-rain':
      return <CloudRain className="w-10 h-10 sm:w-14 sm:h-14 text-blue-500" />;
    case 'thunderstorm':
      return <CloudLightning className="w-10 h-10 sm:w-14 sm:h-14 text-purple-600" />;
    default:
      return <Sun className="w-10 h-10 sm:w-14 sm:h-14 text-amber-500" />;
  }
};

const WeatherCard = ({ data }) => {
  const { t } = useLanguage();
  if (!data || !data.current) return null;

  const { location_name, current, forecast, farming_tip } = data;

  return (
    <div className="space-y-6">
      {/* Current Main Weather Card */}
      <div className="bg-gradient-to-br from-emerald-800 via-emerald-700 to-teal-800 text-white rounded-3xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        {/* Subtle background decoration */}
        <div className="absolute -right-8 -top-8 w-44 h-44 bg-white/10 rounded-full blur-2xl pointer-events-none" />

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-white/20 pb-6">
          <div>
            <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-xs font-bold uppercase tracking-wider mb-2">
              📍 {location_name}
            </span>
            <div className="flex items-baseline gap-3">
              <span className="text-5xl sm:text-7xl font-extrabold tracking-tight">
                {current.temperature}°
              </span>
              <span className="text-2xl sm:text-3xl font-semibold opacity-90">C</span>
            </div>
            <p className="text-lg sm:text-2xl font-bold mt-1 text-emerald-100">
              {current.condition}
            </p>
          </div>

          <div className="bg-white/15 p-4 rounded-3xl backdrop-blur-md flex items-center justify-center self-end sm:self-center shadow-inner">
            {getWeatherIcon(current.icon)}
          </div>
        </div>

        {/* 4 Essential Metrics for Farmers */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-6">
          <div className="bg-white/10 rounded-2xl p-3.5 backdrop-blur-sm border border-white/10">
            <div className="flex items-center gap-2 text-emerald-200 text-xs sm:text-sm font-semibold mb-1">
              <Droplets className="w-4 h-4" />
              <span>{t('weather.humidity')}</span>
            </div>
            <div className="text-xl sm:text-2xl font-extrabold">{current.humidity}%</div>
          </div>

          <div className="bg-white/10 rounded-2xl p-3.5 backdrop-blur-sm border border-white/10">
            <div className="flex items-center gap-2 text-emerald-200 text-xs sm:text-sm font-semibold mb-1">
              <CloudRain className="w-4 h-4" />
              <span>{t('weather.rain_prob')}</span>
            </div>
            <div className="text-xl sm:text-2xl font-extrabold">{current.rain_probability}%</div>
          </div>

          <div className="bg-white/10 rounded-2xl p-3.5 backdrop-blur-sm border border-white/10">
            <div className="flex items-center gap-2 text-emerald-200 text-xs sm:text-sm font-semibold mb-1">
              <Wind className="w-4 h-4" />
              <span>{t('weather.wind')}</span>
            </div>
            <div className="text-xl sm:text-2xl font-extrabold">{current.wind_speed} km/h</div>
          </div>

          <div className="bg-white/10 rounded-2xl p-3.5 backdrop-blur-sm border border-white/10">
            <div className="flex items-center gap-2 text-emerald-200 text-xs sm:text-sm font-semibold mb-1">
              <Compass className="w-4 h-4" />
              <span>{t('weather.current_weather')}</span>
            </div>
            <div className="text-sm sm:text-base font-bold truncate">{current.condition}</div>
          </div>
        </div>
      </div>

      {/* AI Smart Farming Tip for Today */}
      {farming_tip && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-3xl p-5 sm:p-6 shadow-md relative overflow-hidden">
          {data.source === 'fallback' && (
            <div className="mb-4 bg-amber-100/90 border border-amber-400 text-amber-950 rounded-2xl p-3 font-bold text-xs sm:text-sm flex items-center gap-2 shadow-xs">
              <AlertTriangle className="w-4 h-4 text-amber-700 flex-shrink-0" />
              <span>{t('common.offline_demo_banner')}</span>
            </div>
          )}
          <div className="flex items-center gap-2.5 text-amber-900 font-extrabold text-lg sm:text-xl mb-3">
            <Sparkles className="w-6 h-6 text-amber-600 flex-shrink-0" />
            <h3>{t('weather.farming_tip_title')}</h3>
          </div>
          <div className="text-stone-800 text-base sm:text-lg font-medium leading-relaxed whitespace-pre-wrap">
            {farming_tip}
          </div>
        </div>
      )}

      {/* 5-Day Forecast */}
      {forecast && forecast.length > 0 && (
        <div className="bg-white rounded-3xl p-5 sm:p-7 border border-emerald-100 shadow-sm">
          <h3 className="font-extrabold text-lg sm:text-xl text-stone-900 mb-4 flex items-center gap-2">
            <span>📅</span>
            <span>{t('weather.forecast_title')}</span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {forecast.map((day, idx) => (
              <div
                key={day.date || idx}
                className="bg-stone-50 hover:bg-emerald-50/60 transition-colors border border-stone-200 rounded-2xl p-3.5 text-center flex flex-col items-center justify-between gap-2"
              >
                <span className="text-xs font-bold text-stone-600 uppercase">
                  {new Date(day.date).toLocaleDateString('hi-IN', { weekday: 'short', day: 'numeric', month: 'short' })}
                </span>
                <div className="my-1 scale-90">
                  {getWeatherIcon(day.icon)}
                </div>
                <div className="text-sm font-extrabold text-stone-800">
                  {day.temp_max}° / <span className="text-stone-500 font-medium">{day.temp_min}°</span>
                </div>
                <div className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full">
                  💧 {day.rain_probability}%
                </div>
                <div className="text-xs font-semibold text-stone-600 line-clamp-1">
                  {day.condition}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default WeatherCard;
