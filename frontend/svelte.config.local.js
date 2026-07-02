// Local-dev-only SvelteKit config: adapter-static for Docker builds,
// ssr: false for local dev server (prevents OOM).
// The production svelte.config.js (adapter-node, ssr: true) is unchanged.
import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({
			fallback: 'index.html',
			precompress: false
		}),
		ssr: false
	}
};

export default config;
