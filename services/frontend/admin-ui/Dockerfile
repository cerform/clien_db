FROM node:18-alpine AS build
WORKDIR /app
# Copy package.json (and package-lock.json if present) explicitly
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY . ./
RUN npm run build

FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
