FROM node:20-alpine AS build
WORKDIR /app
ARG BUILD_SHA=dev
ENV BUILD_SHA=${BUILD_SHA}
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
# R1 Cluster Alpha (2026-05-12) — run as non-root 'node' user (Alpine default UID 1000).
COPY --from=build --chown=node:node /app/build ./build
COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/package.json ./
USER node
ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000
CMD ["node", "build"]
