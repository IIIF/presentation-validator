ARG version=3.12
FROM python:${version}-slim

WORKDIR /app

# Copy project files
COPY . /app

# Install the project (uses pyproject.toml)
RUN pip install --no-cache-dir .

# Expose port (match your CLI default or override)
EXPOSE 8080

# Run the new CLI
CMD ["iiif-validator", "serve", "--host", "0.0.0.0", "--port", "8080"]