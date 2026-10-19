import React, { useState, useEffect, useRef } from 'react';
import apiClient, { getErrorMessage } from '../api/client';
import { useLanguage } from '../context/LanguageContext';
import WeatherCard from '../components/WeatherCard';
import Loader from '../components/Loader';
import ErrorMessage from '../components/ErrorMessage';
import { Search, MapPin, CloudSun } from 'lucide-react';

const LAST_CITY_KEY = 'kisanmitra_last_city';

const Weather = () => {
  const { t, language } = useLanguage();
  const [cityInput, setCityInput] = useState('');
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Keep track of active query source for language changes
  const activeQueryRef = useRef(null); // { type: 'city', value: '...' } or { type: 'coords', lat, lon }

  // Load last searched city on mount if present; otherwise show empty state prompt
  useEffect(() => {
    try {
      const savedCity = localStorage.getItem(LAST_CITY_KEY);
      if (savedCity && savedCity.trim()) {
        setCityInput(savedCity.trim());
        fetchWeatherByCity(savedCity.trim(), false); // save=false for automatic restore
      }
    } catch (e) {
      console.warn('Failed to read last city from localStorage:', e);
    }
  }, []);

  // Reload weather on language change WITHOUT saving to history (save=false)
  const isFirstMountRef = useRef(true);
  useEffect(() => {
    if (isFirstMountRef.current) {
      isFirstMountRef.current = false;
      return;
    }
    if (activeQueryRef.current) {
      if (activeQueryRef.current.type === 'city') {
        fetchWeatherByCity(activeQueryRef.current.value, false);
      } else if (activeQueryRef.current.type === 'coords') {
        fetchWeatherByCoords(activeQueryRef.current.lat, activeQueryRef.current.lon, false);
      }
    }
  }, [language]);

  const fetchWeatherByCity = async (cityName, saveToHistory = false) => {
    const q = cityName.trim();
    if (!q) return;

    setLoading(true);
    setError('');

    try {
      const response = await apiClient.get('/api/weather', {
        params: {
          city: q,
          language,
          save: saveToHistory ? 'true' : 'false',
        },
      });
      setWeatherData(response.data);
      activeQueryRef.current = { type: 'city', value: q };
      try {
        localStorage.setItem(LAST_CITY_KEY, q);
      } catch (e) {
        console.warn('Failed to save last city to localStorage:', e);
      }
    } catch (err) {
      const defaultErr = `${t('weather.fetch_error_prefix')} '${q}'.`;
      setError(getErrorMessage(err, defaultErr));
    } finally {
      setLoading(false);
    }
  };

  const fetchWeatherByCoords = async (lat, lon, saveToHistory = false) => {
    setLoading(true);
    setError('');

    try {
      const response = await apiClient.get('/api/weather', {
        params: {
          lat,
          lon,
          city: t('weather.my_location'),
          language,
          save: saveToHistory ? 'true' : 'false',
        },
      });
      setWeatherData(response.data);
      activeQueryRef.current = { type: 'coords', lat, lon };
    } catch (err) {
      setError(getErrorMessage(err, t('weather.geo_error_coords')));
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (cityInput.trim()) {
      fetchWeatherByCity(cityInput, true); // save=true for user-initiated search
    }
  };

  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      setError(t('weather.error_geo'));
      return;
    }

    setLoading(true);
    setError('');

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        fetchWeatherByCoords(latitude, longitude, true); // save=true for user location
      },
      () => {
        setLoading(false);
        setError(t('weather.error_geo'));
      },
      { timeout: 10000 }
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight flex items-center gap-3">
          <span>{t('weather.title')}</span>
        </h1>
        <p className="text-base sm:text-lg text-stone-600 font-medium mt-1">
          {t('weather.subtitle')}
        </p>
      </div>

      {/* Search & Location Bar */}
      <div className="bg-white rounded-3xl p-5 sm:p-7 border border-emerald-100 shadow-sm space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              placeholder={t('weather.search_placeholder')}
              className="w-full text-base sm:text-lg bg-stone-50 border-2 border-stone-200 focus:border-emerald-600 focus:bg-white rounded-2xl py-3.5 pl-11 pr-4 outline-none transition-all font-medium"
            />
            <Search className="w-5 h-5 text-stone-400 absolute left-4 top-1/2 -translate-y-1/2" />
          </div>

          <button
            type="submit"
            disabled={loading || !cityInput.trim()}
            className="px-6 py-3.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-extrabold text-base sm:text-lg rounded-2xl transition-all shadow-md active:scale-95 flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>{t('weather.search_btn')}</span>
          </button>
        </form>

        <div className="flex items-center justify-between pt-1">
          <button
            type="button"
            onClick={handleUseLocation}
            disabled={loading}
            className="inline-flex items-center gap-2 text-sm sm:text-base font-bold text-emerald-800 hover:text-emerald-950 bg-emerald-50 hover:bg-emerald-100 px-4 py-2 rounded-xl transition-colors cursor-pointer border border-emerald-200"
          >
            <MapPin className="w-4 h-4 text-emerald-600" />
            <span>{t('weather.geo_btn')}</span>
          </button>

          <span className="text-xs sm:text-sm font-semibold text-stone-500">
            {t('weather.open_meteo_credit')}
          </span>
        </div>
      </div>

      {/* Loading */}
      {loading && <Loader message={t('weather.loading')} />}

      {/* Error */}
      <ErrorMessage
        error={error}
        onRetry={() => {
          setError('');
          if (cityInput.trim()) {
            fetchWeatherByCity(cityInput, false);
          }
        }}
      />

      {/* Empty State Prompt if no city searched yet */}
      {!loading && !weatherData && !error && (
        <div className="bg-white rounded-3xl p-10 sm:p-14 text-center border-2 border-dashed border-emerald-200 space-y-4">
          <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto rounded-3xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
            <CloudSun className="w-8 h-8 sm:w-10 sm:h-10 text-emerald-600" />
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-stone-800">
            {t('weather.search_btn')}
          </h2>
          <p className="text-stone-600 font-medium text-base sm:text-lg max-w-lg mx-auto">
            {t('weather.empty_state_prompt')}
          </p>
        </div>
      )}

      {/* Weather Results Display */}
      {!loading && weatherData && <WeatherCard data={weatherData} />}
    </div>
  );
};

export default Weather;
