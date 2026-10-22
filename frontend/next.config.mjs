/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    // ブラウザからは同一オリジンの /api/backend/* を叩き、
    // Next.js サーバーが Docker ネットワーク内の backend へプロキシする。
    // これにより CORS やホスト名の差異をフロントエンドコードから隠蔽できる。
    const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
