# Projet de session INF349 — API REST de commandes

Application Web (Flask) responsable de prendre des commandes Internet et de
gérer leur paiement. Cette deuxième remise ajoute PostgreSQL, un cache Redis,
le paiement en arrière-plan (RQ), une interface HTML et un déploiement Docker.

## Prérequis

- Python 3.6 ou plus récent
- Docker et Docker Compose (pour PostgreSQL et Redis)

## Architecture

- `api8inf349/` : le code de l'application
  - `__init__.py` : création de l'application Flask, commandes `init-db` et `worker`
  - `models.py` : modèles de la base de données (peewee / PostgreSQL)
  - `routes.py` : les routes de l'API REST
  - `products.py` : récupération des produits depuis le service distant
  - `payment.py` : communication avec le service de paiement distant
  - `cache.py` : connexion Redis, cache des commandes et file de tâches RQ
  - `tasks.py` : tâche de paiement exécutée en arrière-plan par le worker
  - `static/` : pages HTML d'interaction avec l'API
- `Dockerfile` : image Docker de l'application
- `docker-compose.yml` : lance PostgreSQL 12 et Redis 5
- `requirements.txt` : dépendances Python

## Variables d'environnement

L'application est configurée par les variables d'environnement suivantes :

| Variable      | Description                       | Exemple                  |
|---------------|-----------------------------------|--------------------------|
| `FLASK_APP`   | Nom de l'application              | `api8inf349`             |
| `FLASK_DEBUG` | Mode debug                        | `True`                   |
| `DB_HOST`     | Hôte PostgreSQL                   | `localhost`              |
| `DB_USER`     | Utilisateur PostgreSQL            | `user`                   |
| `DB_PASSWORD` | Mot de passe PostgreSQL           | `pass`                   |
| `DB_PORT`     | Port PostgreSQL                   | `5432`                   |
| `DB_NAME`     | Nom de la base de données         | `api8inf349`             |
| `REDIS_URL`   | URL de connexion à Redis          | `redis://localhost`      |

## Installation et lancement

### 1. Lancer PostgreSQL et Redis

```
docker compose up -d
```

Cette commande démarre PostgreSQL 12 (port 5432) et Redis 5 (port 6379).

### 2. Créer un environnement virtuel et installer les dépendances

```
python -m venv venv
venv\Scripts\activate        (Windows)
source venv/bin/activate     (macOS / Linux)
pip install -r requirements.txt
```

### 3. Définir les variables d'environnement

**Windows (PowerShell) :**
```
$env:FLASK_APP="api8inf349"
$env:FLASK_DEBUG="True"
$env:DB_HOST="localhost"
$env:DB_USER="user"
$env:DB_PASSWORD="pass"
$env:DB_PORT="5432"
$env:DB_NAME="api8inf349"
$env:REDIS_URL="redis://localhost"
```

### 4. Initialiser la base de données

```
flask init-db
```

Cette commande crée les tables et charge les produits depuis le service distant.

### 5. Lancer l'application

```
flask run
```

L'application est accessible sur http://127.0.0.1:5000

### 6. Lancer le worker (dans un second terminal)

Le worker traite les paiements en arrière-plan. Il faut définir les mêmes
variables d'environnement dans ce terminal, puis :

```
flask worker
```

Le worker doit tourner en même temps que l'application pour que les paiements
soient traités.

## Interface HTML

Une interface est disponible pour interagir avec l'API :

- http://127.0.0.1:5000/boutique

Elle permet de consulter les produits, créer une commande (avec un ou plusieurs
produits), saisir l'adresse de livraison, payer et consulter une commande.

## Lancement avec Docker

### Construire l'image

```
docker build -t api8inf349 .
```

### Lancer le conteneur

PostgreSQL et Redis doivent tourner (via `docker compose up -d`). Comme
l'application tourne dans un conteneur, on remplace `localhost` par
`host.docker.internal` pour joindre PostgreSQL et Redis :

```
docker run -p 5000:5000 -e REDIS_URL=redis://host.docker.internal -e DB_HOST=host.docker.internal -e DB_USER=user -e DB_PASSWORD=pass -e DB_PORT=5432 -e DB_NAME=api8inf349 api8inf349
```

## Routes de l'API

| Méthode | Route                  | Description                                  |
|---------|------------------------|----------------------------------------------|
| GET     | `/`                    | Liste des produits                           |
| POST    | `/order`               | Créer une commande (un ou plusieurs produits)|
| GET     | `/order/<id>`          | Consulter une commande                       |
| PUT     | `/order/<id>`          | Ajouter email + adresse, ou payer            |

## Fonctionnalités

- Création de commande avec un ou plusieurs produits
- Calcul automatique des taxes (par province) et des frais d'expédition
- Paiement par carte de crédit via un service distant
- Paiement traité en arrière-plan (RQ) : retourne `202` pendant le traitement,
  `409` si un paiement est déjà en cours
- Mise en cache des commandes payées dans Redis (consultables même sans
  PostgreSQL)
- Persistance des erreurs de paiement dans la transaction
