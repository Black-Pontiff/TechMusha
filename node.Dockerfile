FROM node:20-alpine
RUN adduser -D -u 1000 runner
USER runner
WORKDIR /work

