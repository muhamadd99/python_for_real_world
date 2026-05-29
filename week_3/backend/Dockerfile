# Step 1: Use the stable Python 3.14 Bookworm image
FROM python:3.14.4-bookworm

# Step 2: Pin the exact minor version of uv to prevent breaking tool changes
RUN pip install uv==0.8.*

# Step 3: Set up the internal working environment
WORKDIR /app

# Step 4: Copy configuration files from your host root to the container
# This looks into your backend folder to find your package requirements and lockfile
COPY pyproject.toml uv.lock* ./

# Step 5: Pre-install all third-party dependencies (FastAPI, Uvicorn, etc.)
# This layer is completely cached by Docker unless your uv.lock changes!
RUN uv sync --frozen

# Step 6: Copy the week_2 module folder into the container (so main.py can import it)
COPY src/ /app/src/

# Step 7: Expose the port FastAPI runs on
EXPOSE 8000

# Step 8: Configure execution entrypoint utilizing uv environment tracking
ENTRYPOINT ["uv", "run", "uvicorn"]

# Step 9: Run the FastAPI app (assumes main.py is in the root directory of your app)
CMD ["--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "app:app"]