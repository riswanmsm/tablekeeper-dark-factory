FROM mcr.microsoft.com/playwright/python:v1.50.0-noble
# Install curl, git, and Node.js 20+ (needed for Claude Code / Codex CLI / UI builds)
RUN apt-get update && apt-get install -y git curl build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @anthropic-ai/claude-code @openai/codex \
    && rm -rf /var/lib/apt/lists/*
# Install uv for fast Python management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
RUN uv init --bare && uv add "band-sdk[claude-sdk,codex,gemini,langgraph]" python-dotenv pytest httpx playwright
COPY run_seat.py /app/run_seat.py
WORKDIR /workspace
CMD ["uv", "--directory", "/app", "run", "python", "/app/run_seat.py"]