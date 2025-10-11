#!/bin/bash
# Teardown script for ChaosSec infrastructure

set -e

echo "========================================"
echo " ChaosSec Teardown"
echo "========================================"
echo

# Confirm teardown
read -p "Are you sure you want to destroy ChaosSec infrastructure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Teardown cancelled."
    exit 0
fi

echo
echo "Destroying AWS CDK stack..."
cd infrastructure

if command -v cdk &> /dev/null; then
    cdk destroy --force
    echo "✅ CDK stack destroyed"
else
    echo "❌ AWS CDK not found. Cannot destroy infrastructure."
    echo "Install CDK with: npm install -g aws-cdk"
    exit 1
fi

cd ..

echo
echo "Cleaning up local files..."

# Remove generated files (keep evidence for audit)
rm -f chaossec_history.json
echo "✅ History file removed"

echo
echo "Note: Evidence files in ./chaossec_evidence/ are retained for compliance."
echo "To remove evidence, manually delete: rm -rf chaossec_evidence/"
echo

echo "✅ Teardown complete!"
echo

