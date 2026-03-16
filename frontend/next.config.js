/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },

  // Internationalization support
  i18n: {
    locales: ['en', 'ur', 'ar', 'es', 'fr', 'zh'],
    defaultLocale: 'en',
    localeDetection: true,
  },

  // Image optimization
  images: {
    domains: [],
    formats: ['image/avif', 'image/webp'],
  },

  // Performance optimizations
  compress: true,
  poweredByHeader: false,
};

module.exports = nextConfig;
