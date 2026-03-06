Closes #42.

## Technical Changes
- Replaced SSR data loading in `+page.ts` with reactive client-side `$effect` fetching to resolve route navigation desync and crashes.
- Replaced hardcoded 'XWA / Analysis Mode' title with the `<ContentSourceToggle />` component in the header.
- Implemented reactive data fetching based on the global `filters.dataSource` state to seamlessly switch between XWA and Legacy data sets without requiring a page reload.
