import React, { useState, useEffect } from 'react';
import apiClient, { getErrorMessage } from '../api/client';
import { useLanguage } from '../context/LanguageContext';
import WeatherCard from '../components/WeatherCard';
import Loader from '../components/Loader';
import ErrorMessage from '../components/ErrorMessage';
import { Search, MapPin, CloudSun } from 'lucide-react';

const Weather = () => {
  const { t, language } = useLanguage();
  const [cityInput, setCityInput] = useState('');
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Auto-fetch default city on initial mount
  useEffect(() => {
    fetchWeatherByCity('Jaipur');
  }, [language]);

  const fetchWeatherByCity = async (cityName) => {
    const q = cityName.trim();
    if (!q) return;

    setLoading(true);
    setError('');

    try {
      const response = await apiClient.get('/api/weather', {
        params: {
          city: q,
          language,
        },
      });
      setWeatherData(response.data);
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          language === 'hi'
            ? `'${q}' का मौसम डेटा प्राप्त नहीं हो सका। कृपया सही शहर या गांव का नाम लिखें।`
            : `Could not retrieve weather data for '${q}'. Please check the spelling.`
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchWeatherByCoords = async (lat, lon) => {
    setLoading(true);
    setError('');

    try {
      const response = await apiClient.get('/api/weather', {
        params: {
          lat,
          lon,
          city: 'My Location',
          language,
        },
      });
      setWeatherData(response.data);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to retrieve weather for your coordinates.'));
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (cityInput.trim()) {
      fetchWeatherByCity(cityInput);
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
        fetchWeatherByCoords(latitude, longitude);
      },
      (geoError) => {
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
            📡 Open-Meteo Live API
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
          fetchWeatherByCity(cityInput || 'Jaipur');
        }}
      />

      {/* Weather Results Display */}
      {!loading && weatherData && <WeatherCard data={weatherData} />}
    </div>
  );
};

export default Weather;
