# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the container
COPY . .

# Change the working directory to the backend folder
WORKDIR /app/backend

# Expose the port your application runs on (default Flask port is 5000)
EXPOSE 5000

# Set the command to run your application
CMD ["python", "new_app.py"]