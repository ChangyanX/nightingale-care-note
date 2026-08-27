FROM python:3.12-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY services/backend/pyproject.toml services/backend/uv.lock ./
COPY services/backend/app ./app
RUN uv sync --frozen --no-dev
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
