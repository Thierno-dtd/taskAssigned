#!/bin/bash
# Configuration SSL avec Let's Encrypt pour Debian 13

set -e

DOMAIN=${1:-"api.seeg.ga"}
EMAIL=${2:-"admin@seeg.ga"}

echo "=== Configuration SSL pour $DOMAIN ==="

# Installation de Certbot
echo "Installation de Certbot..."
apt-get update
apt-get install -y certbot python3-certbot-nginx

# Arrêter temporairement Nginx pour le challenge
systemctl stop nginx

# Obtenir le certificat
echo "Obtention du certificat SSL..."
certbot certonly --standalone -d $DOMAIN --agree-tos --email $EMAIL --non-interactive

# Configurer Nginx avec SSL
cat > /etc/nginx/sites-available/seeg-intervention <<NGINX
upstream seeg_app {
    server unix:/run/seeg-intervention.sock fail_timeout=0;
}

# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;

    # Configuration SSL sécurisée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 20M;

    location /static/ {
        alias /opt/seeg-intervention/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/seeg-intervention/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://seeg_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINX

# Redémarrer Nginx
systemctl start nginx
nginx -t && systemctl reload nginx

# Configuration du renouvellement automatique
echo "Configuration du renouvellement automatique..."
echo "0 3 * * * certbot renew --quiet --nginx" | crontab -

echo "=== Configuration SSL terminée! ==="
echo "Votre site est maintenant accessible en HTTPS: https://$DOMAIN"
