/**
 * Application Configuration Constants
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://autoballoon-production.up.railway.app/api';
export const APP_URL = import.meta.env.VITE_APP_URL || 'https://autoballoon.space';

// Pricing
export const PRICE_MONTHLY = 99;
export const PRICE_FUTURE = 199;

// Free tier
export const FREE_TIER_LIMIT = 3;

// File upload
export const MAX_FILE_SIZE_MB = 25;
export const ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif'];
