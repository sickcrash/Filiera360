FROM node:18-alpine

WORKDIR /app

# Prima copia solo i file delle dipendenze
COPY package*.json ./

# Poi installa le dipendenze
RUN npm ci

# Infine copia tutto il resto del codice
COPY . .

# Per la live‑reload su filesystem montato da host (opzionale)
ENV CHOKIDAR_USEPOLLING=true \
    HOST=0.0.0.0 \
    PORT=3001

EXPOSE 3001
CMD ["npm", "start"]   
