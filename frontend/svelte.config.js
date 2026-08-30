import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter(),
		csrf: {
			checkOrigin: true,
			trustedOrigins: [
				'http://server-francesco:*',
				'http://server-francesco.gazella-ule.ts.net:*',
				'http://*.gazella-ule.ts.net:*',
				'http://100.69.158.7:*',
				'http://[fd7a:115c:a1e0::613a:9e08]:*',
				'http://localhost:*',
				'http://127.0.0.1:*',
				'https://ko-fi.com',
				'https://*.ko-fi.com',
				'https://m3tacron.com',
				'https://*.m3tacron.com'
			]
		}
	}
};

export default config;
