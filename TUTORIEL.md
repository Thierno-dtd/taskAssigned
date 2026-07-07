# Tutoriel d'utilisation - Application SEEG Intervention

Ce tutoriel explique comment tester et utiliser l'application de gestion d'interventions sur le terrain.

## Table des matières
1. [Installation et démarrage](#1-installation-et-démarrage)
2. [Authentification](#2-authentification)
3. [Gestion des tâches](#3-gestion-des-tâches)
4. [Soumission de rapports](#4-soumission-de-rapports)
5. [Export/Import Excel](#5-exportimport-excel)
6. [Carte GPS](#6-carte-gps)
7. [Tests automatiques](#7-tests-automatiques)

---

## 1. Installation et démarrage

### Prérequis
- Python 3.10+
- PostgreSQL (ou SQLite pour tests)
- pip

### Installation

```bash
# Cloner le projet (si nécessaire)
cd Documents/seeg

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Créer la base de données
python manage.py migrate

# Charger les données de test
python manage.py seed_data
```

### Démarrer le serveur

```bash
python manage.py runserver
```

Accéder à l'application: http://localhost:8000/

Documentation API: http://localhost:8000/api/docs/

Admin Django: http://localhost:8000/admin/

---

## 2. Authentification

L'application supporte deux méthodes d'authentification:

### 2.1 Authentification JWT (classique)

**Obtenir un token:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "agent1", "password": "agent1123"}'
```

**Réponse:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 3,
    "username": "agent1",
    "role": "agent"
  }
}
```

**Utiliser le token:**
```bash
curl -X GET http://localhost:8000/api/tasks/mes-taches/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 2.2 Authentification OTP/SMS (nouvelle)

**Demander un code OTP:**
```bash
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+241 06 12 34 56"}'
```

**Vérifier le code:**
```bash
curl -X POST http://localhost:8000/api/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+241 06 12 34 56", "otp": "123456"}'
```

**Renvoyer un nouveau code:**
```bash
curl -X POST http://localhost:8000/api/auth/otp/resend/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+241 06 12 34 56"}'
```

---

## 3. Gestion des tâches

### 3.1 Voir ses tâches (agent)

```bash
curl -X GET http://localhost:8000/api/tasks/mes-taches/ \
  -H "Authorization: Bearer TOKEN"
```

### 3.2 Voir toutes les tâches (admin/manager)

```bash
# Liste complète
curl -X GET http://localhost:8000/api/tasks/taches/ \
  -H "Authorization: Bearer TOKEN"

# Avec filtres
curl -X GET "http://localhost:8000/api/tasks/taches/?status=pending&semaine=1" \
  -H "Authorization: Bearer TOKEN"
```

### 3.3 Créer une tâche

```bash
curl -X POST http://localhost:8000/api/tasks/taches/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "semaine": 1,
    "titre": "Reparation compteur",
    "description": "Remplacer compteur defectueux",
    "assigne_a": 3,
    "priorite": "high",
    "gps_latitude": "0.4162",
    "gps_longitude": "9.4673",
    "adresse_complet": "Quartier Lalala, Libreville"
  }'
```

### 3.4 Mettre à jour une tâche

```bash
curl -X PATCH http://localhost:8000/api/tasks/taches/1/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### 3.5 Gestion des sous-tâches

**Créer une sous-tâche:**
```bash
curl -X POST http://localhost:8000/api/tasks/taches/1/sous-taches/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "titre": "Verifier installation",
    "description": "Etape 1",
    "ordre": 1,
    "status": "pending"
  }'
```

**Marquer comme terminée:**
```bash
curl -X PATCH http://localhost:8000/api/tasks/sous-taches/1/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "date_realisation": "2026-01-15T10:00:00Z"}'
```

---

## 4. Soumission de rapports

### 4.1 Soumettre un rapport de fin de tâche

```bash
curl -X POST http://localhost:8000/api/reports/rapports/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tache": 1,
    "type_rapport": "completion",
    "commentaire": "Tache effectuee avec succes",
    "latitude": "0.4162",
    "longitude": "9.4673"
  }'
```

### 4.2 Signaler une tâche non effectuée

```bash
curl -X POST http://localhost:8000/api/reports/rapports/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tache": 1,
    "type_rapport": "non_execution",
    "raison_non_execution": "Client absent - porte fermee",
    "categorie_raison": "client",
    "latitude": "0.4162",
    "longitude": "9.4673"
  }'
```

### 4.3 Voir ses rapports (agent)

```bash
curl -X GET http://localhost:8000/api/reports/mes-rapports/ \
  -H "Authorization: Bearer TOKEN"
```

---

## 5. Export/Import Excel

### 5.1 Exporter les tâches

```bash
# Toutes les tâches
curl -X GET http://localhost:8000/api/tasks/export/taches/ \
  -H "Authorization: Bearer TOKEN" \
  -o taches_export.xlsx

# Avec filtres
curl -X GET "http://localhost:8000/api/tasks/export/taches/?semaine_id=1&status=pending" \
  -H "Authorization: Bearer TOKEN" \
  -o taches_filtrees.xlsx
```

### 5.2 Exporter les agents (admin/manager)

```bash
curl -X GET http://localhost:8000/api/tasks/export/agents/ \
  -H "Authorization: Bearer TOKEN" \
  -o agents_export.xlsx
```

### 5.3 Importer des tâches depuis Excel

Le fichier Excel doit contenir les colonnes:
- **Titre** (obligatoire)
- **Semaine_ID** (obligatoire)
- **Agent_Username** (obligatoire)
- **Description** (optionnel)
- **Priorite** (low/medium/high/urgent)
- **Date_debut_prevue** (optionnel, format: YYYY-MM-DD)
- **Date_fin_prevue** (optionnel, format: YYYY-MM-DD)

```bash
curl -X POST http://localhost:8000/api/tasks/import/taches/ \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@nouvelles_taches.xlsx"
```

---

## 6. Carte GPS

### 6.1 Récupérer les tâches avec coordonnées pour la carte

```bash
curl -X GET http://localhost:8000/api/tasks/map/taches/ \
  -H "Authorization: Bearer TOKEN"
```

**Réponse:**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Reparation compteur",
      "coordinates": {
        "latitude": 0.4162,
        "longitude": 9.4673
      },
      "status": "pending",
      "priority": "high"
    }
  ],
  "center": {"latitude": 0.4162, "longitude": 9.4673},
  "zoom": 12
}
```

### 6.2 Suivre les agents en temps réel

```bash
curl -X GET http://localhost:8000/api/tasks/agents/tracking/ \
  -H "Authorization: Bearer TOKEN"
```

### 6.3 Mettre à jour la position d'une tâche

```bash
curl -X POST http://localhost:8000/api/tasks/taches/1/localisation/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 0.4162,
    "longitude": 9.4673,
    "address": "Quartier Lalala, Libreville"
  }'
```

### 6.4 Chercher les tâches proches d'une position

```bash
curl -X GET "http://localhost:8000/api/tasks/map/proches/?lat=0.4162&lng=9.4673&radius_km=5" \
  -H "Authorization: Bearer TOKEN"
```

---

## 7. Tests automatiques

### 7.1 Exécuter tous les tests

```bash
python manage.py test
```

### 7.2 Tests par module

```bash
# Tests du module accounts
python manage.py test accounts

# Tests du module tasks
python manage.py test tasks

# Tests du module reports
python manage.py test reports
```

### 7.3 Tests avec couverture

```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

---

## 8. Scénarios de test complets

### 8.1 Scénario 1: Agent complète une tâche

1. Se connecter en tant qu'agent
2. Voir ses tâches (GET /api/tasks/mes-taches/)
3. Choisir une tâche en attente
4. Mettre à jour le statut "in_progress"
5. Mettre à jour la position GPS
6. Soumettre un rapport de fin avec photo
7. Vérifier dans le dashboard

### 8.2 Scénario 2: Manager assigne des tâches

1. Se connecter en tant que manager
2. Créer une nouvelle semaine
3. Importer des tâches depuis Excel
4. Assigner des tâches aux agents
5. Voir les statistiques dans le dashboard

### 8.3 Scénario 3: Admin utilise OTP

1. Demander un code OTP
2. Vérifier le code affiché dans la console
3. Utiliser le code pour obtenir un token JWT
4. Accéder aux données protégées

---

## Identifiants de test

| Utilisateur | Mot de passe | Rôle |
|-------------|--------------|------|
| admin | admin123 | Administrateur |
| manager1 | manager123 | Manager |
| agent1 | agent1123 | Agent |
| agent2 | agent2123 | Agent |
| agent3 | agent3123 | Agent |
| agent4 | agent4123 | Agent |
| agent5 | agent5123 | Agent |

---

## Support

Pour toute question ou problème:
- Consulter le fichier API_GUIDE.md
- Vérifier la documentation Swagger: http://localhost:8000/api/docs/
- Vérifier les logs du serveur Django

---

*Version 1.0 - Application SEEG Intervention*
