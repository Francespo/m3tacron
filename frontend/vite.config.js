import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

function resolveApiProxyTarget() {
	const raw = process.env.VITE_PROXY_TARGET || process.env.VITE_API_BASE || 'http://backend:8888';
	return raw.replace(/\/api\/?$/, '');
}

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		proxy: {
			'/api': resolveApiProxyTarget()
		}
	}
});
