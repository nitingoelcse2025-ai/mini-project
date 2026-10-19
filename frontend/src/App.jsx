import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useLanguage } from './context/LanguageContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import CropAdvice from './pages/CropAdvice';
import Weather from './pages/Weather';
import Chat from './pages/Chat';
import PlantCheck from './pages/PlantCheck';
import History from './pages/History';

function App() {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen flex flex-col bg-stone-50 text-stone-900 selection:bg-emerald-200">
      {/* Sticky Navbar */}
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-10">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/crop" element={<CropAdvice />} />
          <Route path="/weather" element={<Weather />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/plant" element={<PlantCheck />} />
          <Route path="/history" element={<History />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-emerald-100 py-6 sm:py-8 mt-12 text-center text-stone-600 text-xs sm:text-sm font-semibold">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span>🌾</span>
            <span className="font-bold text-stone-800">KisanMitra AI</span>
            <span>•</span>
            <span>{t('app_tagline')}</span>
          </div>
          <div className="text-stone-500">
            {t('footer_text')}
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
