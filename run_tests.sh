#!/bin/bash
# Run tests script

echo "🧪 Running Tattoo Appointment Bot Tests"
echo "========================================"

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Run: source .venv/bin/activate"
    exit 1
fi

# Install test dependencies if needed
echo "📦 Checking dependencies..."
pip install -q pytest pytest-asyncio pytest-mock pytest-cov

# Run unit tests
echo ""
echo "🧪 Running Unit Tests..."
pytest tests/ -m "not integration" -v

# Check if integration tests should run
if [ "$1" == "--integration" ]; then
    echo ""
    echo "🌐 Running Integration Tests..."
    pytest tests/ -m "integration" -v
fi

# Generate coverage report
echo ""
echo "📊 Generating Coverage Report..."
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html -m "not integration"

echo ""
echo "✅ Tests complete! Coverage report: htmlcov/index.html"
