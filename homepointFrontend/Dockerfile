# Frontend Dockerfile - Multi-stage build
FROM node:20-alpine AS builder

# Set work directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
VITE_API_BASE_URL=https://test.betasys.co.ke/api
RUN npm run build

# Production stage
FROM nginx:alpine

# Set environment variables
ENV NODE_ENV=production

# Set work directory
WORKDIR /app

# Production Stage
FROM nginx:alpine

# Copy built assets from builder stage to Nginx default html folder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy a custom nginx config for Vue (to handle SPA routing)
# This prevents 404 errors when you refresh the page on a sub-route
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


