# Guide API - Gestion Intervention

## Vue d'ensemble

Application Django REST API pour la gestion des interventions terrain avec :
- **Authentication JWT** (JSON Web Tokens)
- **Gestion des utilisateurs** (Admin, Manager, Agent)
- **Gestion des tâches** (Semaines, Tâches, Sous-tâches)
- **Rapports d'exécution** (Terminé/Non effectué avec photos et géolocalisation)
- **Dashboard avec statistiques** (Taux d'exécution, rapports par agent)

---

## Structure du Projet

```
gestion_intervention/
├── accounts/           # Gestion utilisateurs
├── tasks/              # Gestion tâches et sous-tâches
├── reports/            # Rapports d'exécution
├── dashboard/          # Statistiques et graphiques
└── gestion_intervention/  # Configuration projet
```

---

## Points d'accès API

### 🔐 Authentification

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/register/` | Inscription nouvel utilisateur |
| POST | `/api/auth/login/` | Connexion (retourne JWT tokens) |
| POST | `/api/auth/token/refresh/` | Rafraîchir le token d'accès |
| GET | `/api/auth/profile/` | Profil de l'utilisateur connecté |
| GET | `/api/auth/agents/` | Liste des agents (admin/manager) |
| GET | `/api/auth/agents/<id>/` | Détail d'un agent |

**Exemple de login:**
```json
POST /api/auth/login/
{
    "username": "agent1",
    "password": "motdepasse"
}

Response:
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "agent1",
        "email": "agent@example.com",
        "first_name": "Jean",
        "last_name": "Dupont",
        "role": "agent",
        "role_display": "Agent terrain",
        "phone": "+241 06 12 34 56",
        "is_active_agent": true
    }
}
```

---

### 📅 Gestion des Semaines

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/semaines/` | Liste des semaines |
| POST | `/api/semaines/` | Créer une semaine |
| GET | `/api/semaines/<id>/` | Détail d'une semaine |
| PUT/PATCH | `/api/semaines/<id>/` | Modifier une semaine |
| DELETE | `/api/semaines/<id>/` | Supprimer une semaine |

**Exemple de création:**
```json
POST /api/semaines/
{
    "numero": 16,
    "annee": 2025,
    "date_debut": "2025-04-14",
    "date_fin": "2025-04-20",
    "is_active": true
}
```

---

### 📋 Gestion des Tâches

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/taches/` | Liste des tâches (filtrable) |
| POST | `/api/taches/` | Créer une tâche |
| GET | `/api/taches/<id>/` | Détail d'une tâche |
| PUT/PATCH | `/api/taches/<id>/` | Modifier une tâche |
| DELETE | `/api/taches/<id>/` | Supprimer une tâche |
| GET | `/api/mes-taches/` | Tâches de l'agent connecté |
| GET | `/api/semaines/<id>/taches/` | Tâches d'une semaine |

**Filtres disponibles:**
- `?semaine=1` - Par semaine
- `?assigne_a=2` - Par agent assigné
- `?status=pending` - Par statut (pending/in_progress/completed/not_done)
- `?priorite=high` - Par priorité (low/medium/high/urgent)
- `?search=motcle` - Recherche dans titre/description

**Exemple de création:**
```json
POST /api/taches/
{
    "titre": "Réparation compteur électrique",
    "description": "Remplacer le compteur défectueux chez le client",
    "semaine": 1,
    "assigne_a": 2,
    "status": "pending",
    "priorite": "high",
    "date_debut_prevue": "2025-04-15T08:00:00Z",
    "date_fin_prevue": "2025-04-15T12:00:00Z"
}
```

**Statuts possibles:**
- `pending` - En attente
- `in_progress` - En cours
- `completed` - Terminée
- `not_done` - Non effectuée

---

### 🔧 Gestion des Sous-tâches

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/taches/<id>/sous-taches/` | Liste des sous-tâches |
| POST | `/api/taches/<id>/sous-taches/` | Créer une sous-tâche |
| GET | `/api/sous-taches/<id>/` | Détail d'une sous-tâche |
| PUT/PATCH | `/api/sous-taches/<id>/` | Modifier une sous-tâche |
| DELETE | `/api/sous-taches/<id>/` | Supprimer une sous-tâche |

**Exemple de création:**
```json
POST /api/taches/1/sous-taches/
{
    "titre": "Vérifier l'installation",
    "description": "Contrôler l'état des câbles",
    "status": "pending",
    "ordre": 1
}
```

---

### 📝 Rapports d'Exécution

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/rapports/` | Liste des rapports |
| GET | `/api/rapports/<id>/` | Détail d'un rapport |
| POST | `/api/soumettre/` | Soumettre un rapport (simplifié) |
| GET | `/api/mes-rapports/` | Rapports de l'agent connecté |

**Types de rapport:**
- `completion` - Tâche terminée avec succès
- `non_execution` - Tâche non effectuée (avec raison)

**Exemple - Tâche terminée:**
```json
POST /api/soumettre/
{
    "tache": 1,
    "type_rapport": "completion",
    "commentaire": "Compteur remplacé avec succès. Client satisfait.",
    "latitude": 0.4162,
    "longitude": 9.4673
}
```

**Exemple - Tâche non effectuée:**
```json
POST /api/soumettre/
{
    "tache": 1,
    "type_rapport": "non_execution",
    "raison_non_execution": "Client absent malgré rendez-vous confirmé",
    "categorie_raison": "absence",
    "latitude": 0.4162,
    "longitude": 9.4673
}
```

**Catégories de raison:**
- `absence` - Absence client
- `indisponibilite` - Indisponibilité accès
- `materiel` - Problème matériel
- `meteo` - Conditions météo
- `urgence` - Urgence autre
- `autre` - Autre raison

---

### 📊 Dashboard & Statistiques

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/stats/` | Statistiques générales |
| GET | `/api/stats/semaine/` | Stats semaine active |
| GET | `/api/stats/semaine/<id>/` | Stats par semaine |
| GET | `/api/stats/agents/` | Stats par agent (admin) |
| GET | `/api/stats/raisons/` | Analyse des raisons non-exécution |

**Réponse `/api/stats/`:**
```json
{
    "total_taches": 150,
    "taches_terminees": 120,
    "taches_non_executees": 15,
    "taches_en_cours": 10,
    "taches_en_attente": 5,
    "taux_execution": 80.00,
    "taux_non_execution": 10.00,
    "total_sous_taches": 450,
    "sous_taches_terminees": 380
}
```

**Réponse `/api/stats/agents/` (admin uniquement):**
```json
[
    {
        "assigne_a__username": "agent1",
        "assigne_a__first_name": "Jean",
        "assigne_a__last_name": "Dupont",
        "total": 50,
        "terminees": 45,
        "non_executees": 5
    },
    ...
]
```

---

## 🔒 Headers requis

Pour toutes les requêtes authentifiées:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## 📱 Exemple d'utilisation Mobile

```javascript
// 1. Authentification
const loginResponse = await fetch('http://api.example.com/api/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'agent1',
        password: 'password123'
    })
});
const { access, refresh, user } = await loginResponse.json();

// 2. Récupérer mes tâches
const tasksResponse = await fetch('http://api.example.com/api/mes-taches/', {
    headers: {
        'Authorization': `Bearer ${access}`
    }
});
const tasks = await tasksResponse.json();

// 3. Soumettre un rapport
const reportResponse = await fetch('http://api.example.com/api/soumettre/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        tache: 1,
        type_rapport: 'completion',
        commentaire: 'Tâche effectuée avec succès',
        latitude: 0.4162,
        longitude: 9.4673
    })
});
```

---

## 🛠️ Modèles de données

### User (Compte utilisateur)
```python
{
    "id": 1,
    "username": "agent1",
    "email": "agent@example.com",
    "first_name": "Jean",
    "last_name": "Dupont",
    "role": "agent",  # admin/agent/manager
    "phone": "+241 06 12 34 56",
    "is_active_agent": true,
    "date_joined": "2025-04-01T10:00:00Z"
}
```

### Tache
```python
{
    "id": 1,
    "titre": "Réparation compteur",
    "description": "Remplacer compteur défectueux",
    "status": "completed",
    "status_display": "Terminée",
    "priorite": "high",
    "priorite_display": "Haute",
    "semaine": 1,
    "assigne_a": 2,
    "assigne_a_nom": "Jean Dupont",
    "date_creation": "2025-04-10T08:00:00Z",
    "date_debut_prevue": "2025-04-15T08:00:00Z",
    "date_fin_prevue": "2025-04-15T12:00:00Z",
    "date_realisation": "2025-04-15T10:30:00Z",
    "sous_taches_count": 3,
    "sous_taches_terminees": 3
}
```

### RapportExecution
```python
{
    "id": 1,
    "tache": 1,
    "tache_titre": "Réparation compteur",
    "sous_tache": null,
    "sous_tache_titre": null,
    "agent": 2,
    "agent_nom": "Jean Dupont",
    "type_rapport": "completion",
    "type_rapport_display": "Tâche terminée",
    "commentaire": "Travail effectué correctement",
    "photo": "rapports/photos/2025/04/image.jpg",
    "raison_non_execution": null,
    "categorie_raison": null,
    "categorie_raison_display": null,
    "date_soumission": "2025-04-15T10:30:00Z",
    "latitude": "0.416200",
    "longitude": "9.467300"
}
```

---

## 📚 Documentation complémentaire

- **Swagger UI**: http://localhost:8000/api/docs/
- **Schema OpenAPI**: http://localhost:8000/api/schema/
- **Admin Django**: http://localhost:8000/admin/

---

## 🚀 Démarrage rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Créer la base de données
python manage.py migrate

# 3. Créer un super utilisateur
python manage.py createsuperuser

# 4. Lancer le serveur
python manage.py runserver

# 5. Accéder à l'API
# http://localhost:8000/api/docs/
```
