#!/bin/bash
# Setup local complet, en une commande, pour un poste qui vient de cloner
# le repo (ou pour tout réinitialiser proprement sur un poste existant).
#
# Usage : ./setup_dev.sh
#
# Ce que fait ce script :
#   1. Crée un venv Python (si absent)
#   2. Installe les dépendances
#   3. Crée un .env depuis .env.example (si absent), avec une SECRET_KEY
#      générée aléatoirement — jamais le même mot codé en dur deux fois
#   4. Supprime l'ancienne base SQLite locale si elle existe (repart propre)
#   5. Applique les migrations
#   6. Charge les données de démo (agents, tâches, rapports de test)
#   7. Lance le serveur de dev

set -e

echo "=== 1/7 : environnement virtuel ==="
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "=== 2/7 : dépendances ==="
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "=== 3/7 : fichier .env ==="
if [ ! -f ".env" ]; then
    cp .env.example .env
    # Génère une vraie SECRET_KEY aléatoire au lieu de garder celle du .env.example
    GENERATED_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    # Remplace la ligne SECRET_KEY=... par la clé générée (compatible sed GNU et BSD/macOS)
    if sed --version >/dev/null 2>&1; then
        sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${GENERATED_KEY}|" .env
    else
        sed -i '' "s|^SECRET_KEY=.*|SECRET_KEY=${GENERATED_KEY}|" .env
    fi
    echo ".env créé avec une SECRET_KEY générée automatiquement."
else
    echo ".env déjà présent, non modifié."
fi

echo "=== 4/7 : réinitialisation de la base locale ==="
rm -f db.sqlite3

echo "=== 5/7 : migrations ==="
python manage.py migrate

echo "=== 6/7 : données de démo ==="
python manage.py seed_data

echo "=== 7/7 : c'est prêt ! ==="
echo ""
echo "Identifiants de démo : admin / admin123, manager1 / manager123, agent1 / agent1123"
echo "Doc Swagger : http://127.0.0.1:8000/api/docs/"
echo ""
echo "Lancement du serveur (Ctrl+C pour arrêter)..."
python manage.py runserver
