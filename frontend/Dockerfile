# Stage 1: Install dependencies
FROM node:18-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Build the application
FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Environment variables must be passed at build time for Next.js static generation
# We set a placeholder here, but for 'NEXT_PUBLIC_' vars, they usually get baked in at build time.
# For runtime config in Docker, Next.js requires special handling or just baking it in.
# For simplicity, we assume NEXT_PUBLIC_API_URL and NEXT_PUBLIC_WS_URL are passed via build-args or .env.local
ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Stage 3: Run the application
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files for standalone mode
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
# set hostname to 0.0.0.0 to make it accessible outside container
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
