#!/bin/bash
# Setup script for ChaosSec

set -e

echo "========================================"
echo " ChaosSec Setup"
echo "========================================"
echo

# Check Python version
echo "Checking Python version..."
python3 --version || {
    echo "Error: Python 3.11+ required"
    exit 1
}

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo
echo "✅ Python environment setup complete"
echo

# Setup CDK
echo "Setting up AWS CDK..."
cd infrastructure

# Check if Node.js is installed
if command -v node &> /dev/null; then
    echo "Node.js version: $(node --version)"
    
    # Install CDK globally if not installed
    if ! command -v cdk &> /dev/null; then
        echo "Installing AWS CDK CLI..."
        npm install -g aws-cdk
    fi
    
    echo "AWS CDK version: $(cdk --version)"
else
    echo "Warning: Node.js not found. CDK deployment will not be available."
    echo "Install Node.js 18+ to deploy infrastructure."
fi

cd ..

echo
echo "✅ Setup complete!"
echo
echo "Next steps:"
echo "  1. Copy env.example to .env: cp env.example .env"
echo "  2. Edit .env with your AWS credentials and Bedrock API key"
echo "  3. Activate the virtual environment: source venv/bin/activate"
echo "  4. Run the demo: python demo_run.py"
echo "  5. (Optional) Deploy infrastructure: cd infrastructure && cdk deploy"
echo

