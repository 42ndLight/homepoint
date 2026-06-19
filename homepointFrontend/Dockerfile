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

# Custom nginx config for SPA routing (listening on non-privileged port 8080)
RUN echo 'server { \
    listen 8080; \
    include /etc/nginx/mime.types; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Copy and setup entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Ensure nginx user has appropriate permissions for directories it needs to write to
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid

EXPOSE 8080

# Switch to the non-privileged nginx user
USER nginx

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
