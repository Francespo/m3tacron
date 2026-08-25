import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter(),
		// Ko-fi sends server-to-server POST as application/x-www-form-urlencoded
		// with no Origin header. SvelteKit's built-in CSRF blocks form POSTs
		// with missing Origin before hooks.server.ts runs, so
		// https://m3tacron.com/api/support/webhook/ko-fi would 403.
		// Disable the built-in check and re-implement it in hooks.server.ts
		// for every route except the Ko-fi webhook (which is authenticated
		// via verification_token instead).
		csrf: {
			checkOrigin: false
		}
	}
};

export default config;
