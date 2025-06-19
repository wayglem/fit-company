# Use the same Python base image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Enable bytecode compilation and set UV link mode to copy
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy project dependency files
COPY pyproject.toml uv.lock ./

# Copy billing service source code
COPY src/billing ./src/billing

# Copy your main entrypoint
COPY main_billing.py ./main_billing.py

# Install Python dependencies
RUN uv sync

# Set environment variables
ENV FLASK_ENV=development

# Expose the billing service port
EXPOSE 5003

# Start the billing service with uv
CMD ["uv", "run", "main_billing.py"]
