import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

const shouldLogConfig = process.env.VITE_LOG_CONFIG === 'true';

function logConfig(label, value) {
	if (!shouldLogConfig) return;
	console.log(`[vite-config] ${label}`, value);
}

function resolveApiProxyTarget() {
	const raw = process.env.VITE_PROXY_TARGET || process.env.VITE_API_BASE || 'http://backend:8888';
	const resolved = raw.replace(/\/api\/?$/, '');
	logConfig('VITE_PROXY_TARGET_RAW', raw);
	logConfig('VITE_PROXY_TARGET_RESOLVED', resolved);
	return resolved;
}

function resolveAllowedHosts() {
	const raw =
		process.env.VITE_ALLOWED_HOSTS ||
		'localhost,127.0.0.1,.dev.m3tacron.com,dev.m3tacron.com,www.dev.m3tacron.com,.m3tacron.com,m3tacron.com,92.m3tacron.com';

	const resolved = raw
		.split(',')
		.map((host) => host.trim())
		.filter(Boolean);

	logConfig('VITE_ALLOWED_HOSTS_RAW', raw);
	logConfig('VITE_ALLOWED_HOSTS_RESOLVED', resolved);
	return resolved;
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
