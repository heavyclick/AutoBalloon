/**
 * Application Constants & Configuration
 */

// API Base URL - change in production
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Pricing
export const PRICE_MONTHLY = 99;
export const PRICE_FUTURE = 199;

// Free tier limit
export const FREE_TIER_LIMIT = 3;

// App info
export const APP_NAME = 'AutoBalloon';
export const APP_URL = import.meta.env.VITE_APP_URL || 'https://autoballoon.space';

// File upload limits
export const MAX_FILE_SIZE_MB = 25;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
export const ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif'];
