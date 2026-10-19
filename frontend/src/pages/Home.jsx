import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import {
  Sprout,
  CloudSun,
  MessageSquareText,
  ScanEye,
  History,
  PhoneCall,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

const Home = () => {
  const { t } = useLanguage();

  const cards = [
    {
      to: '/crop',
      title: t('home.cta_crop_title'),
      desc: t('home.cta_crop_desc'),
      icon: Sprout,
      color: 'bg-emerald-600',
      lightBg: 'bg-emerald-50 hover:bg-emerald-100/70 border-emerald-200',
      badge: t('home.badge_crop'),
    },
    {
      to: '/weather',
      title: t('home.cta_weather_title'),
      desc: t('home.cta_weather_desc'),
      icon: CloudSun,
      color: 'bg-sky-600',
      lightBg: 'bg-sky-50 hover:bg-sky-100/70 border-sky-200',
      badge: t('home.badge_weather'),
    },
    {
      to: '/chat',
      title: t('home.cta_chat_title'),
      desc: t('home.cta_chat_desc'),
      icon: MessageSquareText,
      color: 'bg-amber-600',
      lightBg: 'bg-amber-50 hover:bg-amber-100/70 border-amber-200',
      badge: t('home.badge_chat'),
    },
    {
      to: '/plant',
      title: t('home.cta_plant_title'),
      desc: t('home.cta_plant_desc'),
      icon: ScanEye,
      color: 'bg-teal-600',
      lightBg: 'bg-teal-50 hover:bg-teal-100/70 border-teal-200',
      badge: t('home.badge_plant'),
    },
    {
      to: '/history',
      title: t('home.cta_history_title'),
      desc: t('home.cta_history_desc'),
      icon: History,
      color: 'bg-stone-700',
      lightBg: 'bg-stone-100 hover:bg-stone-200/70 border-stone-300',
      badge: t('home.badge_history'),
    },
  ];

  return (
    <div className="space-y-10 sm:space-y-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-emerald-900 via-emerald-800 to-green-900 text-white p-7 sm:p-14 shadow-xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-700/80 border border-emerald-500/30 text-emerald-100 text-xs sm:text-sm font-bold tracking-wide">
            <span className="animate-pulse">🌱</span>
            <span>{t('home.badge')}</span>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
            {t('home.hero_title')}
          </h1>

          <p className="text-base sm:text-xl text-emerald-100 font-medium leading-relaxed">
            {t('home.hero_subtitle')}
          </p>

          {/* Quick CTA Buttons */}
          <div className="pt-2 flex flex-wrap gap-3 sm:gap-4">
            <Link
              to="/crop"
              className="px-6 py-3.5 rounded-2xl bg-white text-emerald-900 font-extrabold text-base sm:text-lg hover:bg-emerald-50 active:scale-95 transition-all shadow-md flex items-center gap-2"
            >
              <span>{t('home.cta_crop_title')}</span>
              <ArrowRight className="w-5 h-5 text-emerald-700" />
            </Link>

            <Link
              to="/chat"
              className="px-6 py-3.5 rounded-2xl bg-emerald-700/80 hover:bg-emerald-700 text-white font-extrabold text-base sm:text-lg active:scale-95 transition-all border border-emerald-500/40 flex items-center gap-2"
            >
              <span>{t('home.cta_chat_title')}</span>
              <MessageSquareText className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* 5 Main Feature Cards */}
      <section className="space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900">
            {t('home.main_features_title')}
          </h2>
          <span className="text-sm font-semibold text-stone-500 hidden sm:inline">
            {t('home.main_features_subtitle')}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
          {cards.map((card) => {
            const Icon = card.icon;
            return (
              <Link
                key={card.to}
                to={card.to}
                className={`p-6 sm:p-7 rounded-3xl border-2 transition-all duration-200 group flex flex-col justify-between shadow-sm hover:shadow-lg hover:-translate-y-1 ${card.lightBg}`}
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className={`w-14 h-14 rounded-2xl ${card.color} text-white flex items-center justify-center shadow-md group-hover:scale-110 transition-transform`}
                    >
                      <Icon className="w-7 h-7" />
                    </div>
                    <span className="text-xs font-bold px-3 py-1 bg-white rounded-full shadow-xs text-stone-700 border border-stone-200">
                      {card.badge}
                    </span>
                  </div>

                  <h3 className="text-xl sm:text-2xl font-extrabold text-stone-900 mb-2 group-hover:text-emerald-800 transition-colors">
                    {card.title}
                  </h3>

                  <p className="text-sm sm:text-base text-stone-700 font-medium leading-relaxed">
                    {card.desc}
                  </p>
                </div>

                <div className="pt-5 flex items-center gap-2 text-sm sm:text-base font-extrabold text-stone-900 group-hover:text-emerald-700">
                  <span>{t('home.open_feature')}</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1.5 transition-transform" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Why Farmers Love KisanMitra */}
      <section className="bg-white rounded-3xl p-6 sm:p-10 border border-emerald-100 shadow-sm space-y-6">
        <h2 className="text-xl sm:text-2xl font-extrabold text-stone-900 flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-emerald-600" />
          <span>{t('home.quick_guide_title')}</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
          <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-100 flex items-start gap-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm sm:text-base font-bold text-stone-800">
              {t('home.benefit1')}
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-100 flex items-start gap-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm sm:text-base font-bold text-stone-800">
              {t('home.benefit2')}
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-100 flex items-start gap-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm sm:text-base font-bold text-stone-800">
              {t('home.benefit3')}
            </p>
          </div>
        </div>

        {/* Farmer Helpline Banner */}
        <div className="p-4 sm:p-5 rounded-2xl bg-amber-50 border border-amber-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-amber-950">
          <div className="flex items-center gap-3">
            <PhoneCall className="w-6 h-6 text-amber-700 flex-shrink-0" />
            <div>
              <span className="font-extrabold text-base">{t('home.kcc_title')}: </span>
              <span className="font-bold text-lg text-amber-900">1800-180-1551 ({t('home.toll_free')})</span>
            </div>
          </div>
          <span className="text-xs font-bold text-amber-800 bg-amber-200/60 px-3 py-1 rounded-full">
            {t('home.govt_helpline')}
          </span>
        </div>
      </section>
    </div>
  );
};

export default Home;
