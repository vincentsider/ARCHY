#!/bin/bash

# Change to the backend directory
cd "$(dirname "$0")"

# Install required packages
pip install -r requirements.txt

# Start the FastAPI application
uvicorn main:app --reload --port 8002
