#!/bin/bash
# Development environment setup script for NEUIToolkit

set -e  # Exit on error

echo "=========================================="
echo "NEUIToolkit Development Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version detected"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Install main dependencies
echo "Installing main dependencies..."
pip install -r requirements.txt --quiet
echo "✓ Main dependencies installed"
echo ""

# Install development dependencies
echo "Installing development dependencies..."
pip install pytest pytest-cov black flake8 mypy isort bandit pydocstyle pre-commit --quiet
echo "✓ Development dependencies installed"
echo ""

# Install pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install
echo "✓ Pre-commit hooks installed"
echo ""

# Run pre-commit on all files (optional)
read -p "Run pre-commit checks on all files now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running pre-commit on all files..."
    pre-commit run --all-files || true
    echo "✓ Pre-commit checks complete"
fi
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your API keys!"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Download spaCy model (optional)
read -p "Download spaCy English model? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Downloading spaCy model..."
    python -m spacy download en_core_web_sm --quiet
    echo "✓ spaCy model downloaded"
fi
echo ""

echo "=========================================="
echo "✓ Development environment ready!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Edit .env file and add your API keys"
echo ""
echo "  3. Run tests to verify setup:"
echo "     pytest"
echo ""
echo "  4. Start developing!"
echo "     - Format code: black backend/ llm/ tests/"
echo "     - Lint code: flake8 backend/ llm/ tests/"
echo "     - Type check: mypy backend/ llm/"
echo "     - Run tests: pytest --cov=backend --cov=llm"
echo ""
echo "Pre-commit hooks will run automatically on git commit."
echo "=========================================="
