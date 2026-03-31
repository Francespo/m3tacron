import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

function resolveApiProxyTarget() {
	const raw = process.env.VITE_PROXY_TARGET || process.env.VITE_API_BASE || 'http://backend:8888';
	return raw.replace(/\/api\/?$/, '');
}

function resolveAllowedHosts() {
	const raw =
		process.env.VITE_ALLOWED_HOSTS ||
		'localhost,127.0.0.1,.dev.m3tacron.com,dev.m3tacron.com,www.dev.m3tacron.com,.m3tacron.com,m3tacron.com,www.m3tacron.com';

	return raw
		.split(',')
		.map((host) => host.trim())
		.filter(Boolean);
}

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		allowedHosts: resolveAllowedHosts(),
		proxy: {
			'/api': resolveApiProxyTarget()
		}
	}
});
