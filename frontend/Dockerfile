# Build stage
FROM node:20-slim AS builder

WORKDIR /app
ENV NODE_OPTIONS=--max-old-space-size=2048
COPY frontend/package*.json ./
RUN npm install
COPY frontend .
COPY external_data /tmp/external_data
RUN rm -rf static/data-legacy static/data-xwa || true
RUN rm -rf static/fonts/xwing-miniatures-font || true
RUN mkdir -p static/data-legacy static/data-xwa static/fonts/xwing-miniatures-font
RUN if [ -d /tmp/external_data/xwing-data2-legacy/data ]; then cp -a /tmp/external_data/xwing-data2-legacy/data/. static/data-legacy/; fi
RUN if [ -d /tmp/external_data/xwing-data2/data ]; then cp -a /tmp/external_data/xwing-data2/data/. static/data-xwa/; fi
RUN if [ -d /tmp/external_data/xwing-miniatures-font/dist ]; then cp -a /tmp/external_data/xwing-miniatures-font/dist/. static/fonts/xwing-miniatures-font/; fi

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
