/** @type {import('next').NextConfig} */

const apiBackend = (
  process.env.API_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.VERCEL ? "https://nyayalens-production.up.railway.app" : "http://localhost:8000")
).replace(/\/$/, "");

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiBackend}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
