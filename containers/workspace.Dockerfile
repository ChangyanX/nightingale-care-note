FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm
RUN pip install --no-cache-dir uv pre-commit
WORKDIR /workspace
