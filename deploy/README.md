# Guide de Déploiement - SEEG Intervention

Ce répertoire contient les scripts et configurations pour déployer l'application SEEG Intervention.

## Structure

```
deploy/
├── debian13/           # Déploiement serveur Debian 13
│   ├── install.sh      # Script d'installation complet
│   ├── setup-ssl.sh    # Configuration SSL Let's Encrypt
│   └── .env.example    # Exemple de configuration
└── docker/            # (Optionnel) Configuration Docker
```

## Déploiement sur Debian 13

### Prérequis

- Serveur Debian 13 fraîchement installé
- Accès root ou sudo
- Nom de domaine configuré (ex: api.seeg.ga)
- Ports 80 et 443 ouverts

### Étapes rapides

1. **Copier le script d'installation**
```bash
scp deploy/debian13/install.sh root@api.seeg.ga:/tmp/
scp deploy/debian13/.env.example root@api.seeg.ga:/tmp/
```

2. **Exécuter l'installation**
```bash
ssh root@api.seeg.ga
chmod +x /tmp/install.sh
/tmp/install.sh
```

3. **Configurer l'application**
```bash
cd /opt/seeg-intervention
cp deploy/debian13/.env.example .env
nano .env  # Modifier les paramètres
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

4. **Configurer SSL (optionnel mais recommandé)**
```bash
/tmp/setup-ssl.sh api.seeg.ga admin@seeg.ga
```

5. **Redémarrer les services**
```bash
supervisorctl restart seeg-intervention
systemctl restart nginx
```

### Variables d'environnement importantes

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DEBUG` | Mode debug | `False` |
| `SECRET_KEY` | Clé secrète Django | `votre-cle-secrete` |
| `ALLOWED_HOSTS` | Hôtes autorisés | `api.seeg.ga,localhost` |
| `DATABASE_URL` | URL de la base de données | `postgres://user:pass@localhost/db` |
| `REDIS_URL` | URL Redis | `redis://localhost:6379/0` |

## Architecture de déploiement

```
┌─────────────────────────────────────────────────────────────┐
│                     Apache2 (Reverse Proxy)                   │
│  - SSL/TLS termination                                        │
│  - Static files serving (DocumentRoot /var/www/html/seeg)   │
│  - Load balancing (optionnel)                                 │
└────────────────────┬──────────────────────────────────────┘
                     │
┌────────────────────┴──────────────────────────────────────┐
│                  Gunicorn (WSGI Server)                   │
│  - Unix socket: /run/seeg-intervention.sock               │
│  - Multiple worker processes                              │
└────────────────────┬──────────────────────────────────────┘
                     │
┌────────────────────┴──────────────────────────────────────┐
│                  Django Application                        │
│  - API REST                                                │
│  - Authentication JWT/OTP                                  │
│  - Business logic                                          │
└────────────────────────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
PostgreSQL       Redis         File Storage
(Database)       (Cache/Queue)   (Media/Static)
```

## Commandes utiles

### Gestion des services

```bash
# Redémarrer l'application
supervisorctl restart seeg-intervention

# Voir les logs
supervisorctl tail seeg-intervention

# Status des services
systemctl status apache2
systemctl status postgresql
systemctl status redis-server
supervisorctl status
```

### Mise à jour de l'application

```bash
cd /opt/seeg-intervention
source venv/bin/activate

# Tirer les nouvelles modifications (si git)
git pull origin main

# Mettre à jour les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Redémarrer
supervisorctl restart seeg-intervention
```

### Sauvegarde de la base de données

```bash
# Sauvegarde
sudo -u postgres pg_dump seeg-intervention > backup_$(date +%Y%m%d).sql

# Restauration
sudo -u postgres psql seeg-intervention < backup_20240115.sql
```

## Sécurité

### Firewall (UFW)

```bash
# Status
ufw status

# Autoriser un port
ufw allow 8080/tcp

# Bloquer une IP
ufw deny from 192.168.1.100
```

### Mise à jour automatique des certificats SSL

Le script `setup-ssl.sh` configure déjà le renouvellement automatique via cron.

Pour vérifier:
```bash
certbot renew --dry-run
```

## Monitoring

### Logs importants

```bash
# Application Django
tail -f /opt/seeg-intervention/logs/gunicorn.log
tail -f /opt/seeg-intervention/logs/error.log

# Apache2
tail -f /var/log/apache2/seeg-intervention-error.log
tail -f /var/log/apache2/seeg-intervention-access.log

# PostgreSQL
tail -f /var/log/postgresql/postgresql-15-main.log
```

## Dépannage

### L'application ne démarre pas

1. Vérifier les permissions
2. Vérifier les variables d'environnement
3. Vérifier les logs: `supervisorctl tail seeg-intervention`

### Erreur 502 Bad Gateway

1. Vérifier que Gunicorn tourne: `supervisorctl status`
2. Vérifier le socket: `ls -la /run/seeg-intervention.sock`
3. Vérifier la configuration Apache2: `apache2ctl configtest`

### Base de données inaccessible

```bash
# Vérifier PostgreSQL
sudo -u postgres psql -c "\l"

# Vérifier les connexions
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

## Support

Pour toute assistance:
- Consulter le fichier `TUTORIEL.md`
- Vérifier la documentation API: `https://api.seeg.ga/api/docs/`
- Contacter l'équipe technique
