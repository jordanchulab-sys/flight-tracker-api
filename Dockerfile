# Use an official lightweight Python image
FROM python:3.11-slim

# Create a non-privileged system user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY lookup_flight.py .

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-privileged user
USER appuser

# Run the script when the container starts
CMD ["python", "lookup_flight.py"]