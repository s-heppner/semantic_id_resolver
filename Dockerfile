# Use the official Alpine Linux as the base image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the package files to the working directory
COPY . .

# Install system dependencies
RUN apk update && apk add --no-cache git

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set PYTHONPATH to the app directory
ENV PYTHONPATH=/app

# Expose the port that FastAPI will run on
EXPOSE 8125

# Command to run the FastAPI server
CMD ["python", "semantic_id_resolver/service.py"]
