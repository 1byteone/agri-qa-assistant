/** @type {import('next').NextConfig} */
const backendOrigin = process.env.BACKEND_ORIGIN || 'http://localhost:8001'

const nextConfig = {
  // Keep hot-reload artifacts isolated from the production build. This avoids
  // webpack-runtime referencing a chunk removed by another Next process.
  distDir: process.env.NEXT_DIST_DIR || (process.env.NODE_ENV === 'development' ? '.next-dev' : '.next'),
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/chat',
        destination: `${backendOrigin}/chat`,
      },
      {
        source: '/api/chat/stream',
        destination: `${backendOrigin}/chat/stream`,
      },
      {
        source: '/api/history/:path*',
        destination: `${backendOrigin}/history/:path*`,
      },
      {
        source: '/api/threads/:path*',
        destination: `${backendOrigin}/threads/:path*`,
      },
      {
        source: '/api/threads',
        destination: `${backendOrigin}/threads`,
      },
      {
        source: '/api/health',
        destination: `${backendOrigin}/health`,
      },
      {
        source: '/api/mcp/status',
        destination: `${backendOrigin}/mcp/status`,
      },
      {
        source: '/api/knowledge-base/documents/analyze',
        destination: `${backendOrigin}/knowledge-base/documents/analyze`,
      },
      {
        source: '/api/knowledge-base/documents',
        destination: `${backendOrigin}/knowledge-base/documents`,
      },
      {
        source: '/api/knowledge-base/status',
        destination: `${backendOrigin}/knowledge-base/status`,
      },
      {
        source: '/api/knowledge-base/search',
        destination: `${backendOrigin}/knowledge-base/search`,
      },
      {
        source: '/api/evidence-sources',
        destination: `${backendOrigin}/evidence-sources`,
      },
      {
        source: '/api/evaluations/:path*',
        destination: `${backendOrigin}/evaluations/:path*`,
      },
      {
        source: '/api/agri-terms/lookup',
        destination: `${backendOrigin}/agri-terms/lookup`,
      },
      {
        source: '/api/news',
        destination: `${backendOrigin}/news`,
      },
      {
        source: '/api/resource-image',
        destination: `${backendOrigin}/resource-image`,
      },
    ]
  },
}

module.exports = nextConfig
