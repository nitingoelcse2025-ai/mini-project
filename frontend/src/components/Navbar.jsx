import React, { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import LanguageToggle from './LanguageToggle';
import {
  Sprout,
  CloudSun,
  MessageSquareText,
  ScanEye,
  History,
  Home,
  Menu,
  X,
} from 'lucide-react';

const Navbar = () => {
  const { t } = useLanguage();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { to: '/', label: t('nav_home'), icon: Home },
    { to: '/crop', label: t('nav_crop'), icon: Sprout },
    { to: '/weather', label: t('nav_weather'), icon: CloudSun },
    { to: '/chat', label: t('nav_chat'), icon: MessageSquareText },
    { to: '/plant', label: t('nav_plant'), icon: ScanEye },
    { to: '/history', label: t('nav_history'), icon: History },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-emerald-100 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16 sm:h-20">
          {/* Logo & Brand */}
          <Link
            to="/"
            className="flex items-center gap-2 group"
            onClick={() => setMobileMenuOpen(false)}
          >
            <span className="text-2xl sm:text-3xl select-none group-hover:scale-110 transition-transform">
              🌾
            </span>
            <div className="flex flex-col">
              <span className="font-extrabold text-lg sm:text-2xl text-emerald-900 tracking-tight leading-tight">
                KisanMitra AI
              </span>
              <span className="text-[10px] sm:text-xs font-semibold text-emerald-700 tracking-wider uppercase">
                किसान मित्र
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1 lg:gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-semibold transition-all ${
                      isActive
                        ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-200'
                        : 'text-stone-700 hover:text-emerald-700 hover:bg-emerald-50'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Action Items: Lang Toggle & Mobile Menu button */}
          <div className="flex items-center gap-2 sm:gap-3">
            <LanguageToggle />

            {/* Mobile Hamburger Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              type="button"
              className="md:hidden p-2 rounded-xl bg-stone-100 text-stone-800 hover:bg-emerald-50 hover:text-emerald-800 transition-colors"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-emerald-100 bg-white px-4 pt-3 pb-6 space-y-2 shadow-lg animate-in slide-in-from-top-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl text-base font-bold transition-all ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-md shadow-emerald-200'
                      : 'text-stone-800 hover:bg-emerald-50 hover:text-emerald-900 active:bg-emerald-100'
                  }`
                }
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>
      )}
    </header>
  );
};

export default Navbar;
