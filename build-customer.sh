#!/bin/bash

# Interactive build script for Homepoint Frontend
echo "------------------------------------------------"
echo "Homepoint Customer Build System"
echo "------------------------------------------------"

# Prompt for configuration
read -p "Customer Name (e.g., Hardware Plus): " STORE_NAME
read -p "API Base URL (e.g., https://api.customer.com): " API_URL
read -p "Store TIN: " STORE_TIN
read -p "Store Address: " STORE_ADDRESS
read -p "Store Phone: " STORE_PHONE

# Create a tag name based on store name (lowercase, no spaces)
TAG_NAME=$(echo $STORE_NAME | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

echo "------------------------------------------------"
echo "Building for: $STORE_NAME"
echo "Tag: homepoint-frontend:$TAG_NAME"
echo "------------------------------------------------"

# Build the docker image
# We pass these as ARGs if we want them as defaults, 
# but they will also be configurable at runtime.
docker build -t "homepoint-frontend:$TAG_NAME" \
  --build-arg VITE_API_BASE_URL="$API_URL" \
  --build-arg VITE_STORE_NAME="$STORE_NAME" \
  --build-arg VITE_STORE_TIN="$STORE_TIN" \
  --build-arg VITE_STORE_ADDRESS="$STORE_ADDRESS" \
  --build-arg VITE_STORE_PHONE="$STORE_PHONE" \
  ./homepointFrontend

echo "------------------------------------------------"
echo "Build complete!"
echo "To run this instance:"
echo "docker run -p 8080:80 \\"
echo "  -e VITE_API_BASE_URL=\"$API_URL\" \\"
echo "  -e VITE_STORE_NAME=\"$STORE_NAME\" \\"
echo "  homepoint-frontend:$TAG_NAME"
