import { sentrySvelteKit } from '@sentry/sveltekit';
import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { execSync } from 'node:child_process';

function gitSha(): string {
  try {
    return execSync('git rev-parse --short=7 HEAD', { encoding: 'utf8' }).trim();
  } catch {
    return process.env.BUILD_SHA || 'dev';
  }
}

export default defineConfig({
  plugins: [
    // Phase B4 — Sentry plugin for stack frame normalization. We disable
    // sourcemap upload to GlitchTip in alpha (perf + privacy considerations) ;
    // re-enable later via sourceMapsUploadOptions.org + auth token.
    sentrySvelteKit({ sourceMapsUploadOptions: { org: undefined } }),
    tailwindcss(),
    sveltekit(),
  ],
  define: {
    __APP_VERSION__: JSON.stringify(gitSha()),
  },
});
