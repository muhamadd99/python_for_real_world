FROM python:3.14.4-bookworm

RUN pip install uv==0.8.*

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen

COPY . .

EXPOSE 8000

ENTRYPOINT ["uv", "run", "uvicorn"]
CMD ["--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "app:app"]