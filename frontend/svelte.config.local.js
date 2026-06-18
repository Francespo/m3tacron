// Local-dev-only SvelteKit config: uses adapter-static so the build
// produces a fully static SPA that can be served with any static server.
// The production svelte.config.js (adapter-node) is unchanged.
//
// Usage in Dockerfile.local: this file is copied to svelte.config.js
// before building.
import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({
			fallback: 'index.html',
			precompress: false
		})
	}
};

export default config;
