# Gestion Intervention - Application de Gestion des Tâches Terrain

Application Django avec API REST pour la gestion des tâches d'équipes d'intervention sur le terrain.

## Architecture

### Backend Django
- **Accounts** : Gestion des utilisateurs (admin, manager, agent)
- **Tasks** : Gestion des semaines, tâches et sous-tâches
- **Reports** : Soumission des rapports d'exécution (terminé/non effectué)
- **Dashboard** : Statistiques et graphes pour le suivi

### API REST
- Authentification JWT (JSON Web Tokens)
- Documentation API avec Swagger/OpenAPI
- CORS activé pour les applications mobiles
- Filtrage et pagination

## Installation

### Prérequis
- Python 3.10+
- PostgreSQL (optionnel, SQLite par défaut)

### 1. Cloner le projet

```bash
git clone <repository-url>
cd gestion_intervention
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer la base de données

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Créer un super utilisateur

```bash
python manage.py createsuperuser
```

### 6. Lancer le serveur

```bash
python manage.py runserver
```

## Documentation API

Une fois le serveur démarré :
- API Docs (Swagger) : http://localhost:8000/api/docs/
- Schema API : http://localhost:8000/api/schema/
- Admin Django : http://localhost:8000/admin/

## Endpoints API Principaux

### Authentification
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/login/` - Connexion (JWT)
- `POST /api/auth/token/refresh/` - Rafraîchir token
- `GET /api/auth/profile/` - Profil utilisateur

### Tâches
- `GET /api/taches/` - Liste des tâches
- `POST /api/taches/` - Créer une tâche
- `GET /api/taches/<id>/` - Détail d'une tâche
- `GET /api/mes-taches/` - Tâches de l'agent connecté
- `GET /api/semaines/<id>/taches/` - Tâches par semaine

### Sous-tâches
- `GET /api/taches/<id>/sous-taches/` - Liste des sous-tâches
- `POST /api/taches/<id>/sous-taches/` - Créer une sous-tâche

### Rapports
- `POST /api/soumettre/` - Soumettre un rapport
- `GET /api/mes-rapports/` - Rapports de l'agent

### Dashboard / Statistiques
- `GET /api/stats/` - Statistiques générales
- `GET /api/stats/agents/` - Stats par agent (admin)
- `GET /api/stats/raisons/` - Raisons des non-exécutions

## Structure des Modèles

### User (accounts)
- `role` : admin / manager / agent
- `phone`, `is_active_agent`

### Tache (tasks)
- `titre`, `description`, `status` (pending/in_progress/completed/not_done)
- `semaine`, `assigne_a`, `priorite`
- `date_realisation`

### SousTache (tasks)
- `tache` (FK), `titre`, `description`
- `status`, `ordre`, `date_realisation`

### RapportExecution (reports)
- `tache` ou `sous_tache` (FK)
- `type_rapport` : completion / non_execution
- `commentaire`, `photo`
- `raison_non_execution`, `categorie_raison`
- `latitude`, `longitude` (géolocalisation)

## Application Mobile

L'API est prête pour consommation par une application mobile (React Native, Flutter, etc.).

### Authentification Mobile
1. Login avec username/password → reçoit access + refresh token
2. Stocker les tokens
3. Envoyer `Authorization: Bearer <access_token>` dans les headers

### Exemple d'utilisation mobile

```javascript
// Login
const login = await fetch('http://api-url/api/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'agent1', password: 'pass' })
});

// Récupérer mes tâches
const tasks = await fetch('http://api-url/api/mes-taches/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

// Soumettre un rapport
const report = await fetch('http://api-url/api/soumettre/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    tache: 1,
    type_rapport: 'completion',
    commentaire: 'Tâche effectuée',
    latitude: 4.0511,
    longitude: 9.7679
  })
});
```

## Fonctionnalités Dashboard

- **Taux d'exécution** : Pourcentage de tâches terminées
- **Taux de non-exécution** : Pourcentage de tâches non effectuées
- **Statistiques par agent** : Performance individuelle (admin)
- **Statistiques par semaine** : Suivi hebdomadaire
- **Raisons des non-exécutions** : Analyse des problèmes

## Développement

### Créer des données de test

```python
# Dans Django shell
python manage.py shell

from accounts.models import User
from tasks.models import Semaine, Tache

# Créer un agent
agent = User.objects.create_user(
    username='agent1',
    password='test123',
    role='agent',
    first_name='Jean',
    last_name='Dupont'
)

# Créer une semaine
semaine = Semaine.objects.create(
    numero=15,
    annee=2025,
    date_debut='2025-04-07',
    date_fin='2025-04-13'
)

# Créer une tâche
tache = Tache.objects.create(
    titre='Réparation compteur',
    description='Remplacer compteur défectueux',
    semaine=semaine,
    assigne_a=agent,
    priorite='high'
)
```
