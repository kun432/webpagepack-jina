FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

WORKDIR /workspace

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
