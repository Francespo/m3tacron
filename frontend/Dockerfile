# Build stage
FROM node:20-slim AS builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend .
RUN rm -rf static/data-legacy static/data-xwa || true
COPY external_data/xwing-data2-legacy/data static/data-legacy
COPY external_data/xwing-data2/data static/data-xwa
RUN mkdir -p static/fonts
COPY external_data/xwing-miniatures-font/dist static/fonts/xwing-miniatures-font

# Pass build arguments for SvelteKit environment variables
ARG VITE_API_BASE
ENV VITE_API_BASE=$VITE_API_BASE

RUN npx svelte-kit sync
RUN npm run build

# Production stage
FROM node:20-slim

WORKDIR /app

COPY --from=builder /app/package*.json ./
RUN npm install --omit=dev

COPY --from=builder /app/build ./build

EXPOSE 3333

ENV NODE_ENV=production
ENV PORT=3333
CMD ["node", "build"]
