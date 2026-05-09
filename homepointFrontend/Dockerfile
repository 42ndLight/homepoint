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
RUN npm run build

# Production stage
FROM node:20-alpine

# Set environment variables
ENV NODE_ENV=production

# Set work directory
WORKDIR /app

# Install serve to run production build
RUN npm install -g serve

# Copy built assets from builder stage
COPY --from=builder /app/dist ./dist

# 1. Create the group with GID 1001
# 2. Create the user with UID 1001 and add to group 'appuser'
RUN addgroup -S -g 1001 appuser && \
    adduser -S -u 1001 -G appuser appuser

# 3. Switch to the new user
USER appuser

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5173/ || exit 1

# Start the application
CMD ["serve", "-s", "dist", "-l", "5173"]
