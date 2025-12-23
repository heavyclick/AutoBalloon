/**
 * Footer Component
 * Simple footer with links and copyright
 */

import React from 'react';
import { Link } from 'react-router-dom';

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-[#0a0a0a] border-t border-[#1a1a1a] py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-white">
              Auto<span className="text-[#E63946]">Balloon</span>
            </span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-8 text-sm">
            <a 
              href="mailto:support@autoballoon.space"
              className="text-gray-400 hover:text-white transition-colors"
            >
              Support
            </a>
            <Link 
              to="/privacy"
              className="text-gray-400 hover:text-white transition-colors"
            >
              Privacy
            </Link>
            <Link 
              to="/terms"
              className="text-gray-400 hover:text-white transition-colors"
            >
              Terms
            </Link>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-8 border-t border-[#1a1a1a] text-center">
          <p className="text-gray-500 text-sm">
            © {currentYear} AutoBalloon. All rights reserved.
          </p>
          <p className="text-gray-600 text-xs mt-2">
            Made with precision for manufacturing QC teams
          </p>
        </div>
      </div>
    </footer>
  );
}
