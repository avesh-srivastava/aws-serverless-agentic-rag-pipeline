#!/bin/bash

# Create OpenSearch Lambda Layer
# This script creates a Lambda layer with OpenSearch dependencies

set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-ap-south-1}
LAYER_NAME="opensearch-dependencies-${ENVIRONMENT}"

echo "🔧 Creating OpenSearch Lambda Layer: $LAYER_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create layer directory structure
LAYER_DIR="dist/layers/opensearch"
mkdir -p "$LAYER_DIR/python"

echo -e "${YELLOW}📦 Installing OpenSearch dependencies...${NC}"

# Install dependencies to layer directory
pip install -r src/shared/layers/open-search-dependencies.txt -t "$LAYER_DIR/python" --quiet

echo -e "${YELLOW}🗜️ Creating layer ZIP package...${NC}"

# Create layer ZIP
cd "$LAYER_DIR"
python -c "
import zipfile
import os

def create_layer_zip():
    with zipfile.ZipFile('../opensearch-layer.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('python'):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                # Skip .pyc files
                if file.endswith('.pyc'):
                    continue
                file_path = os.path.join(root, file)
                zipf.write(file_path, file_path)

create_layer_zip()
"
cd - > /dev/null

echo -e "${YELLOW}🚀 Publishing Lambda layer...${NC}"

# Publish layer
LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name "$LAYER_NAME" \
    --description "OpenSearch dependencies for Agentic RAG pipeline" \
    --zip-file "fileb://dist/layers/opensearch-layer.zip" \
    --compatible-runtimes python3.9 python3.10 python3.11 \
    --region "$REGION" \
    --query 'Version' \
    --output text)

echo -e "${GREEN}✅ Layer created successfully!${NC}"
echo -e "${BLUE}📋 Layer Details:${NC}"
echo "Layer Name: $LAYER_NAME"
echo "Version: $LAYER_VERSION"
echo "Region: $REGION"

# Save layer ARN for deployment script
LAYER_ARN="arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):layer:$LAYER_NAME:$LAYER_VERSION"
echo "Layer ARN: $LAYER_ARN"

# Save to config file
mkdir -p "infrastructure/configs"
echo "{\"opensearch_layer_arn\": \"$LAYER_ARN\"}" > "infrastructure/configs/layer-config-$ENVIRONMENT.json"

echo -e "${GREEN}🎉 OpenSearch layer ready for use!${NC}"