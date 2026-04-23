import { sentrySvelteKit } from '@sentry/sveltekit';
import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    // Phase B4 — Sentry plugin for stack frame normalization. We disable
    // sourcemap upload to GlitchTip in alpha (perf + privacy considerations) ;
    // re-enable later via sourceMapsUploadOptions.org + auth token.
    sentrySvelteKit({ sourceMapsUploadOptions: { org: undefined } }),
    tailwindcss(),
    sveltekit(),
  ],
});
