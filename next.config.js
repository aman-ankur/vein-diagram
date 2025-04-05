/** @type {import('next').NextConfig} */
module.exports = {
  // No special server-side processing needed for a SPA
  // This config acts as a hint to Vercel about how to handle routing
  trailingSlash: false,
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/:path*',
        destination: '/index.html',
      },
    ];
  },
}; 