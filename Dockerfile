# ===== Build stage =====
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libxml2-dev libxslt1-dev libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --wheel-dir=/wheels -r requirements.txt

# ===== Runtime stage =====
FROM python:3.11-slim AS runtime

ENV TZ=Asia/Taipei \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安裝必要系統套件 + supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata ca-certificates curl supervisor libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# 安裝 ngrok
ARG NGROK_VERSION=3.13.0
RUN set -eux; \
    ARCH="$(dpkg --print-architecture)"; \
    case "$ARCH" in \
      amd64) NG_ARCH=amd64 ;; \
      arm64) NG_ARCH=arm64 ;; \
      armhf) NG_ARCH=arm ;; \
      *) echo "Unsupported arch: $ARCH" && exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/ngrok.tgz "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v${NGROK_VERSION}-linux-${NG_ARCH}.tgz"; \
    tar -xzf /tmp/ngrok.tgz -C /usr/local/bin; \
    ngrok version

WORKDIR /app

# 安裝 Python 套件
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/*

# 複製程式與 supervisord 設定
COPY . .
COPY supervisord.conf /etc/supervisor/supervisord.conf

# 非 root 執行
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000 4040

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]