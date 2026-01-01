/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  webpack: (config, { isServer }) => {
    // pdf.js worker configuration
    config.resolve.alias.canvas = false;
    config.resolve.alias.encoding = false;

    // Ignore localforage on server
    if (isServer) {
      config.resolve.alias.localforage = false;
    }

    return config;
  },
  // Use standalone output for Railway deployment
  output: 'standalone',
  // Environment variables
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    NEXT_PUBLIC_GOOGLE_VISION_API_KEY: process.env.NEXT_PUBLIC_GOOGLE_VISION_API_KEY,
    NEXT_PUBLIC_GEMINI_API_KEY: process.env.NEXT_PUBLIC_GEMINI_API_KEY,
  },
}

module.exports = nextConfig
