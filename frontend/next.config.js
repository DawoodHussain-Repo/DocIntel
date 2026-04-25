/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: ".next-build",
  experimental: {
    // Reduce/avoid child-process worker spawning in restricted Windows environments.
    cpus: 1,
    workerThreads: true,
  },
};

module.exports = nextConfig;
