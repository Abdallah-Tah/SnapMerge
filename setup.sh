#!/bin/bash

# SnapMerge Setup Script
echo "🔥 Setting up SnapMerge - Image to PDF Converter"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup Backend
echo ""
echo "🐍 Setting up Backend..."
cd backend

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Backend setup complete!"

# Setup Frontend
echo ""
echo "⚛️ Setting up Frontend..."
cd ../frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Install additional dependencies
echo "Installing additional dependencies..."
npm install lucide-react

echo "✅ Frontend setup complete!"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To start the application:"
echo "1. Start Backend:  cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "2. Start Frontend: cd frontend && npm run dev"
echo ""
echo "Then open http://localhost:3000 in your browser!"
