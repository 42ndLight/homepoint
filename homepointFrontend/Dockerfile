# Frontend Dockerfile - Multi-stage build
FROM node:20-alpine AS builder

# Declare the arguments
ARG VITE_API_BASE_URL
ARG VITE_STORE_NAME
ARG VITE_STORE_TIN
ARG VITE_STORE_ADDRESS
ARG VITE_STORE_PHONE

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_STORE_NAME=$VITE_STORE_NAME
ENV VITE_STORE_TIN=$VITE_STORE_TIN
ENV VITE_STORE_ADDRESS=$VITE_STORE_ADDRESS
ENV VITE_STORE_PHONE=$VITE_STORE_PHONE

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy and setup entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Custom nginx config for SPA routing
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
