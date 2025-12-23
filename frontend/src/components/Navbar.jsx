/**
 * Navbar Component
 * Top navigation with logo, links, and auth status
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ProBadge } from './ProBadge';

export function Navbar() {
  const { user, isPro, logout } = useAuth();

  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-40 bg-[#0d0d0d]/90 backdrop-blur-md border-b border-[#1a1a1a]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <img 
              src="/logo.png" 
              alt="AutoBalloon" 
              className="h-8 w-auto"
              onError={(e) => {
                // Fallback if logo doesn't exist
                e.target.style.display = 'none';
              }}
            />
            <span className="text-xl font-bold text-white">
              Auto<span className="text-[#E63946]">Balloon</span>
            </span>
            {isPro && <ProBadge />}
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-8">
            <button 
              onClick={() => scrollToSection('pricing')}
              className="text-gray-400 hover:text-white transition-colors"
            >
              Pricing
            </button>
            <button 
              onClick={() => scrollToSection('faq')}
              className="text-gray-400 hover:text-white transition-colors"
            >
              FAQ
            </button>
          </div>

          {/* Auth Section */}
          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-4">
                <span className="text-gray-400 text-sm hidden sm:block">
                  {user.email}
                </span>
                <button
                  onClick={logout}
                  className="text-gray-400 hover:text-white transition-colors text-sm"
                >
                  Log out
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="bg-[#1a1a1a] hover:bg-[#252525] text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
              >
                Log in
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
