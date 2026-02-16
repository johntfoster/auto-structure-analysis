FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY . .

# Install uv and sync dependencies
RUN pip install uv && uv sync

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
