import React, { createContext, useContext, useState, useEffect } from 'react';
import enTranslations from '../i18n/en.json';
import hiTranslations from '../i18n/hi.json';

const LanguageContext = createContext();

const translations = {
  en: enTranslations,
  hi: hiTranslations,
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguageState] = useState(() => {
    return localStorage.getItem('kisanmitra_lang') || 'hi';
  });

  useEffect(() => {
    localStorage.setItem('kisanmitra_lang', language);
    document.documentElement.lang = language;
  }, [language]);

  const toggleLanguage = () => {
    setLanguageState((prev) => (prev === 'hi' ? 'en' : 'hi'));
  };

  const setLanguage = (lang) => {
    if (lang === 'hi' || lang === 'en') {
      setLanguageState(lang);
    }
  };

  /**
   * Helper to fetch translation strings via dotted keys like 'home.hero_title' or top-level 'app_name'
   */
  const t = (key) => {
    const currentDict = translations[language] || translations.hi;
    const fallbackDict = translations.en;

    const resolve = (dict, path) => {
      const parts = path.split('.');
      let current = dict;
      for (const part of parts) {
        if (current && typeof current === 'object' && part in current) {
          current = current[part];
        } else {
          return null;
        }
      }
      return current;
    };

    const val = resolve(currentDict, key);
    if (val !== null && val !== undefined) return val;

    const fallbackVal = resolve(fallbackDict, key);
    if (fallbackVal !== null && fallbackVal !== undefined) return fallbackVal;

    return key;
  };

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
