#!/bin/bash
# Railway deployment setup script

echo "🚀 Setting up Building Defect Detector for Railway..."

# Download spaCy language model
python -m spacy download en_core_web_sm

echo "✅ Setup complete!"
