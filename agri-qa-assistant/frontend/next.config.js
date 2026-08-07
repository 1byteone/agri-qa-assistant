/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/chat',
        destination: 'http://localhost:8000/chat',
      },
      {
        source: '/api/history/:path*',
        destination: 'http://localhost:8000/history/:path*',
      },
      {
        source: '/api/health',
        destination: 'http://localhost:8000/health',
      },
    ]
  },
}

module.exports = nextConfig