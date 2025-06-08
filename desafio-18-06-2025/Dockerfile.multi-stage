# Stage 1: the builder image, used to build the virtual environment
FROM python:3.13-bookworm AS builder

RUN pip install uv==0.6.12

ENV UV_CACHE_DIR=/tmp/uv_cache

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv venv
RUN . .venv/bin/activate
RUN --mount=type=cache,target=$UV_CACHE_DIR uv sync --no-dev --no-install-project

# Stage 2: the runtime image, used to just run the code provided its virtual environment
FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY streamlit_app.py streamlit_app.py
COPY ai_agents_crew ai_agents_crew

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]