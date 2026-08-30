import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import { execSync } from 'node:child_process';

const shouldLogConfig = process.env.VITE_LOG_CONFIG === 'true';

/**
 * Log a labeled config value to the console when VITE_LOG_CONFIG is true.
 * @param {string} label
 * @param {unknown} value
 */
function logConfig(label, value) {
	if (!shouldLogConfig) return;
	console.log(`[vite-config] ${label}`, value);
}

function logEnvSnapshot() {
	if (!shouldLogConfig) return;

	const visibleKeys = Object.keys(process.env || {})
		.filter((key) => /^(VITE_|COOLIFY_|SERVICE_|ORIGIN$|ALLOWED_ORIGINS$|NODE_ENV$|ENV_VAR_SOURCE$)/.test(key))
		.sort();

	/** @type {Record<string, string | undefined>} */
	const envSummary = {};
	for (const key of visibleKeys) {
		envSummary[key] = process.env[key];
	}

	logConfig('ENV_VAR_SOURCE', process.env.ENV_VAR_SOURCE);
	logConfig('ENV_VALUES', envSummary);
}

function resolveApiProxyTarget() {
	const raw = process.env.VITE_PROXY_TARGET || process.env.VITE_API_BASE;
	const resolved = raw ? raw.replace(/\/api\/?$/, '') : undefined;
	logConfig('VITE_PROXY_TARGET_RAW', raw);
	logConfig('VITE_PROXY_TARGET_RESOLVED', resolved);
	return resolved;
}

// Ensure we never return an empty string as proxy target
function resolveSafeApiProxyTarget() {
	const t = resolveApiProxyTarget();
	if (!t || String(t).trim() === '') return undefined;
	return t;
}

function getTailscaleHosts() {
	const hosts = [];
	try { const ip4 = execSync('tailscale ip -4 2>/dev/null', { encoding: 'utf8' }).trim(); if (ip4) hosts.push(ip4); } catch {}
	try { const ip6 = execSync('tailscale ip -6 2>/dev/null', { encoding: 'utf8' }).trim(); if (ip6) hosts.push(ip6); } catch {}
	try {
		const raw = execSync('tailscale status --json 2>/dev/null', { encoding: 'utf8' });
		const data = JSON.parse(raw);
		const self = data.Self || {};
		const dnsName = (self.DNSName || '').replace(/\.$/, '').trim();
		if (dnsName) hosts.push(dnsName);
		if (self.HostName) hosts.push(self.HostName.trim());
		const suffix = (data.MagicDNSSuffix || data.CurrentTailnet?.MagicDNSSuffix || '').trim();
		if (suffix && self.HostName) { const fqdn = `${self.HostName.trim()}.${suffix.replace(/^\./, '')}`; if (!hosts.includes(fqdn)) hosts.push(fqdn); }
	} catch {}
	return hosts;
}

function resolveAllowedHosts() {
	const raw = process.env.VITE_ALLOWED_HOSTS;
	const tsHosts = getTailscaleHosts();
	if (tsHosts.length) logConfig('VITE_TAILSCALE_HOSTS', tsHosts);
	if (!raw) {
		if (tsHosts.length) {
			const resolved = [...new Set(['localhost', '127.0.0.1', ...tsHosts])];
			logConfig('VITE_ALLOWED_HOSTS_RAW', raw);
			logConfig('VITE_ALLOWED_HOSTS_RESOLVED', resolved);
			return resolved;
		}
		logConfig('VITE_ALLOWED_HOSTS_RAW', raw);
		logConfig('VITE_ALLOWED_HOSTS_RESOLVED', undefined);
		return undefined;
	}
	const normalized = raw.trim().toLowerCase();
	if (normalized === 'true') { logConfig('VITE_ALLOWED_HOSTS_RAW', raw); logConfig('VITE_ALLOWED_HOSTS_RESOLVED', true); return true; }
	const fromEnv = raw.split(',').map((h) => h.trim()).filter(Boolean);
	const merged = [...new Set([...fromEnv, ...tsHosts])];
	for (const h of ['localhost', '127.0.0.1']) if (!merged.includes(h)) merged.push(h);
	logConfig('VITE_ALLOWED_HOSTS_RAW', raw);
	logConfig('VITE_ALLOWED_HOSTS_RESOLVED', merged);
	return merged;
}

logEnvSnapshot();

const allowedHosts = resolveAllowedHosts();
const proxyTarget = resolveApiProxyTarget();

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		...(allowedHosts ? { allowedHosts } : {}),
		...(proxyTarget
			? {
					proxy: {
						'/api': resolveSafeApiProxyTarget()
					}
				}
			: {})
	}
});
