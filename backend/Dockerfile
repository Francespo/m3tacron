FROM python:3.12-slim

WORKDIR /app

ARG INSTALL_PLAYWRIGHT_BROWSER=false

# Install system dependencies for Playwright only when explicitly requested.
RUN if [ "$INSTALL_PLAYWRIGHT_BROWSER" = "true" ]; then \
    apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*; \
    fi

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN if [ "$INSTALL_PLAYWRIGHT_BROWSER" = "true" ]; then playwright install chromium; fi

# Copy application code
COPY . .
COPY external_data /tmp/external_data

RUN if [ ! -d /tmp/external_data/xwing-data2/data ] || [ ! -d /tmp/external_data/xwing-data2-legacy/data ]; then \
    apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*; \
    rm -rf /tmp/external_data; \
    git clone --depth 1 --recurse-submodules https://github.com/Francespo/xwing-unified-data.git /tmp/external_data; \
    fi \
    && mkdir -p /app/external_data \
    && cp -a /tmp/external_data/. /app/external_data/ \
    && rm -rf /tmp/external_data

EXPOSE 8888

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8888 --workers ${UVICORN_WORKERS:-2}"]
