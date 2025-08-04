#!/bin/bash

# Download spaCy model if not present
echo "🔧 Setting up spaCy model..."
python -m spacy download en_core_web_sm || echo "⚠️ SpaCy model download failed, app will run without advanced NLP"

# Start the application
echo "🚀 Starting Building Defect Detector..."
exec gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1
