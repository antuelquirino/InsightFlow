/** @type {import('next').NextConfig} */

const nextConfig = {
  // Next 16 writes AGENTS.md/CLAUDE.md for AI agents; the repo has its own CLAUDE.md.
  agentRules: false,
  redirects: async () => {
    return [
      {
        source: "/",
        destination: "/overview",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
