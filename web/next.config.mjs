/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",            // fully static -> deploy on Vercel's CDN, no backend
  images: { unoptimized: true },
  reactStrictMode: true,
};

export default nextConfig;
