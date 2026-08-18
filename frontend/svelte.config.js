import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		// Use the Node adapter explicitly for Docker/Coolify deployments.
		adapter: adapter()
	}
};

export default config;
