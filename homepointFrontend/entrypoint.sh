#!/bin/sh

# Create the config.js file dynamically inside the Nginx directory
# We use property names that match the expectations in src/services/api.js
echo "window.config = {
  API_BASE_URL: '${VITE_API_BASE_URL}',
  STORE_NAME: '${VITE_STORE_NAME}',
  STORE_TIN: '${VITE_STORE_TIN}',
  STORE_ADDRESS: '${VITE_STORE_ADDRESS}',
  STORE_PHONE: '${VITE_STORE_PHONE}'
};" > /usr/share/nginx/html/config.js

# Execute the main Docker command (starts Nginx)
exec "$@"
