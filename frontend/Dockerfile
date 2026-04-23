# ---------- Base ----------
FROM node:24-slim AS base
WORKDIR /app
ENV NODE_ENV=production

# ---------- Dependencies ----------
FROM base AS deps

# Install minimal system dependencies (needed for some native modules)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=development

COPY package.json package-lock.json* ./
RUN npm ci

# ---------- Builder ----------
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the Next.js app
RUN npm run build

# ---------- Runner ----------
FROM base AS runner
ENV NODE_ENV=production

# Create non-root user
RUN groupadd --system nodejs && useradd --system --gid nodejs nextjs

WORKDIR /app

# Copy only necessary output
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Set permissions (important for some environments)
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
