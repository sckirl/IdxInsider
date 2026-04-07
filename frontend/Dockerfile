FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Expose port
EXPOSE 3000

# Start command
CMD ["npm", "run", "dev"]
