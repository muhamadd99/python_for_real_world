FROM python:3.14-slim

WORKDIR /app

COPY index.html /app/index.html
COPY assets /app/assets
COPY src /app/src
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip \
	&& pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1

EXPOSE 3000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000"]
