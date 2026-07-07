#!/bin/bash
# Script de déploiement pour Debian 13
# Application SEEG Intervention Django

set -e

APP_NAME="seeg-intervention"
APP_USER="obrice"
APP_DIR="/opt/$APP_NAME"
DOMAIN=${DOMAIN:-"api.seeg.ga"}

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "${GREEN}=== Installation SEEG Intervention sur Debian 13 ===${NC}"

# 1. Mise à jour du système
echo "${YELLOW}1. Mise à jour du système...${NC}"
apt-get update && apt-get upgrade -y

# 2. Installation des dépendances
echo "${YELLOW}2. Installation des dépendances...${NC}"
apt-get install -y \
    python3 python3-pip python3-venv \
    postgresql postgresql-contrib \
    apache2 libapache2-mod-wsgi-py3 redis-server supervisor \
    git curl wget \
    libpq-dev python3-dev \
    build-essential pkg-config

# 3. Configuration PostgreSQL
echo "${YELLOW}3. Configuration PostgreSQL...${NC}"
systemctl start postgresql
systemctl enable postgresql

# Créer la base de données et l'utilisateur
sudo -u postgres psql <<EOF
CREATE DATABASE seeg;
CREATE USER obrice WITH PASSWORD 'azerty';
ALTER ROLE obrice SET client_encoding TO 'utf8';
ALTER ROLE obrice SET default_transaction_isolation TO 'read committed';
ALTER ROLE obrice SET timezone TO 'Africa/Libreville';
GRANT ALL PRIVILEGES ON DATABASE seeg TO obrice;
EOF

# 4. Créer l'utilisateur applicatif
echo "${YELLOW}4. Création de l'utilisateur applicatif...${NC}"
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
fi

# 5. Créer le répertoire de l'application
echo "${YELLOW}5. Configuration du répertoire de l'application...${NC}"
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

# 6. Cloner le projet (à adapter selon votre repository)
echo "${YELLOW}6. Déploiement du code source...${NC}"
# git clone https://github.com/votre-repo/seeg-intervention.git $APP_DIR
# OU copier les fichiers depuis une archive
echo "Copiez vos fichiers sources dans $APP_DIR"
echo "Exemple: scp -r /chemin/local/* root@$DOMAIN:$APP_DIR/"

# 7. Créer l'environnement virtuel
echo "${YELLOW}7. Création de l'environnement virtuel...${NC}"
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 8. Configuration Gunicorn
echo "${YELLOW}8. Configuration Gunicorn...${NC}"
mkdir -p $APP_DIR/logs

cat > $APP_DIR/gunicorn_config.py <<'GUNICORN'
import multiprocessing

bind = "unix:/run/seeg-intervention.sock"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
worker_tmp_dir = "/dev/shm"
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

timeout = 30
graceful_timeout = 30

user = "obrice"
group = "obrice"

accesslog = "/opt/seeg-intervention/logs/access.log"
errorlog = "/opt/seeg-intervention/logs/error.log"
loglevel = "info"

capture_output = True
enable_stdio_inheritance = True

proc_name = "seeg-intervention"
GUNICORN

# 9. Configuration Apache2
echo "${YELLOW}9. Configuration Apache2...${NC}"

# Activer les modules nécessaires
a2enmod proxy
a2enmod proxy_http
a2enmod headers
a2enmod rewrite

cat > /etc/apache2/sites-available/$APP_NAME.conf <<'APACHE'
<VirtualHost *:80>
    ServerName api.seeg.ga
    ServerAlias localhost
    DocumentRoot /var/www/html/seeg

    # Logs
    ErrorLog ${APACHE_LOG_DIR}/seeg-intervention-error.log
    CustomLog ${APACHE_LOG_DIR}/seeg-intervention-access.log combined

    # Limite de taille pour les uploads (20MB)
    LimitRequestBody 20971520

    # Fichiers statiques depuis /var/www/html/seeg
    Alias /static/ /var/www/html/seeg/static/
    <Directory /var/www/html/seeg/static>
        Require all granted
        Options -Indexes
    </Directory>

    # Fichiers médias
    Alias /media/ /var/www/html/seeg/media/
    <Directory /var/www/html/seeg/media>
        Require all granted
        Options -Indexes
    </Directory>

    # Proxy vers Gunicorn
    ProxyPreserveHost On
    ProxyPass /static/ !
    ProxyPass /media/ !
    ProxyPass / unix:/run/seeg-intervention.sock|http://127.0.0.1/
    ProxyPassReverse / unix:/run/seeg-intervention.sock|http://127.0.0.1/

    # En-têtes pour le proxy
    RequestHeader set X-Real-IP %{REMOTE_ADDR}s
    RequestHeader set X-Forwarded-For %{REMOTE_ADDR}s
    RequestHeader set X-Forwarded-Proto %{REQUEST_SCHEME}s

    <Proxy *>
        Require all granted
    </Proxy>
</VirtualHost>
APACHE

# Désactiver le site par défaut et activer notre site
a2dissite 000-default
a2ensite $APP_NAME.conf

# 10. Configuration Supervisor
echo "${YELLOW}10. Configuration Supervisor...${NC}"
cat > /etc/supervisor/conf.d/$APP_NAME.conf <<'SUPERVISOR'
[program:seeg-intervention]
command=/opt/seeg-intervention/venv/bin/gunicorn -c /opt/seeg-intervention/gunicorn_config.py gestion_intervention.wsgi:application
directory=/opt/seeg-intervention
user=obrice
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/seeg-intervention/logs/gunicorn.log
environment=DJANGO_SETTINGS_MODULE="gestion_intervention.settings_production"
SUPERVISOR

# 11. Créer les répertoires pour les fichiers statiques et médias
echo "${YELLOW}11. Configuration des fichiers statiques et médias...${NC}"
mkdir -p $APP_DIR/staticfiles
mkdir -p $APP_DIR/media
chown -R $APP_USER:$APP_USER $APP_DIR/staticfiles
chown -R $APP_USER:$APP_USER $APP_DIR/media

# Créer les répertoires dans DocumentRoot Apache
mkdir -p /var/www/html/seeg/static
mkdir -p /var/www/html/seeg/media
chown -R www-data:www-data /var/www/html/seeg/static
chown -R www-data:www-data /var/www/html/seeg/media
chmod -R 755 /var/www/html/seeg

# 12. Configuration systemd pour le socket Gunicorn
cat > /etc/systemd/system/seeg-intervention.socket <<'SOCKET'
[Unit]
Description=SEEG Intervention Gunicorn Socket

[Socket]
ListenStream=/run/seeg-intervention.sock
SocketMode=0666

[Install]
WantedBy=sockets.target
SOCKET

# 13. Redémarrer les services
echo "${YELLOW}13. Redémarrage des services...${NC}"
systemctl daemon-reload
systemctl restart postgresql
systemctl restart redis-server
systemctl restart apache2
supervisorctl reread
supervisorctl update
supervisorctl restart seeg-intervention

# 14. Configuration firewall
echo "${YELLOW}14. Configuration du firewall...${NC}"
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

echo "${GREEN}=== Installation terminée! ===${NC}"
echo ""
echo "${YELLOW}Prochaines étapes:${NC}"
echo "1. Copiez vos fichiers sources dans $APP_DIR"
echo "2. Configurez le fichier .env avec vos paramètres"
echo "3. Exécutez: cd $APP_DIR && source venv/bin/activate"
echo "4. Exécutez: python manage.py migrate"
echo "5. Exécutez: python manage.py collectstatic --noinput"
echo "5b. Copiez les fichiers: cp -r /opt/seeg-intervention/staticfiles/* /var/www/html/seeg/static/"
echo "6. Exécutez: python manage.py createsuperuser"
echo "7. Exécutez: python manage.py seed_data (optionnel)"
echo "8. Redémarrez: supervisorctl restart seeg-intervention"
echo ""
echo "Accès: http://$DOMAIN ou http://$(hostname -I | awk '{print $1}')"
