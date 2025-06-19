# Use the same Python base image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Copy poetry/uv project files for dependency management
COPY pyproject.toml uv.lock ./

# Copy the entire stats source code
COPY src/stats ./src/stats

COPY main_stats.py ./main_stats.py


# Install dependencies
RUN uv sync

# Set environment variables
ENV FLASK_ENV=development

# Expose the port your stats service runs on
EXPOSE 5002

# Run the stats app with uv
CMD ["uv","run", "main_stats.py"]
