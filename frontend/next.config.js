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
        source: '/api/chat/stream',
        destination: 'http://localhost:8000/chat/stream',
      },
      {
        source: '/api/threads',
        destination: 'http://localhost:8000/threads',
      },
      {
        source: '/api/news',
        destination: 'http://localhost:8000/news',
      },
      {
        source: '/api/weather',
        destination: 'http://localhost:8000/weather',
      },
      {
        source: '/api/knowledge-base/status',
        destination: 'http://localhost:8000/knowledge-base/status',
      },
      {
        source: '/api/knowledge-base/search',
        destination: 'http://localhost:8000/knowledge-base/search',
      },
      {
        source: '/api/knowledge-graph/status',
        destination: 'http://localhost:8000/knowledge-graph/status',
      },
      {
        source: '/api/knowledge-graph/search',
        destination: 'http://localhost:8000/knowledge-graph/search',
      },
      {
        source: '/api/system/info',
        destination: 'http://localhost:8000/system/info',
      },
      {
        source: '/api/evidence-sources',
        destination: 'http://localhost:8000/evidence-sources',
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
