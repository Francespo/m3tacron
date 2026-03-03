<script>
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<nav class="main-nav">
	<a href="/" class="nav-brand">M3taCron</a>
	<a href="/ships">Ships</a>
</nav>

{@render children()}

<style>
	.main-nav {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		padding: 0.75rem 1.5rem;
		background: #111122;
		border-bottom: 1px solid #333;
	}

	.main-nav a {
		color: #ccc;
		text-decoration: none;
		font-size: 0.95rem;
	}

	.main-nav a:hover {
		color: #fff;
	}

	.nav-brand {
		font-weight: 700;
		font-size: 1.1rem;
		color: #6c63ff !important;
		margin-right: auto;
	}
</style>
