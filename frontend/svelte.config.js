import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter(),
		csrf: {
			checkOrigin: true,
			trustedOrigins: ['http://server-francesco:*', 'http://100.69.158.7:*', 'http://localhost:*', 'http://127.0.0.1:*']
		}
	}
};

export default config;
