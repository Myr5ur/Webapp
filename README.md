# Projet de session INF349 — API REST de commandes

**Équipe :** Corentin Carvalho · Ahmed Boumaiza · Thomas Lempereur

Application Web (Flask) responsable de prendre des commandes Internet et de
gérer leur paiement. Cette deuxième remise ajoute PostgreSQL, un cache Redis,
le paiement en arrière-plan (RQ), une interface HTML et un déploiement Docker.

## Objectifs

- Se familiariser avec le développement Web
- Développer une API REST
- Utiliser des services Web distants
- S'assurer de la résilience et de la performance d'une application Web
- Utiliser un gestionnaire de tâches
- Déployer une application Web

## Prérequis

- Python 3.6 ou plus récent
- Docker et Docker Compose (pour PostgreSQL et Redis)

## Structure du projet

```
Web/
├── api8inf349/
│   ├── static/
│   │   ├── boutique.html      # Interface web complète (multi-produits, paiement asynchrone)
│   │   └── test.html          # Page de test manuel
│   ├── __init__.py            # Création de l'application Flask, commandes init-db et worker
│   ├── cache.py                # Connexion Redis, file de tâches RQ, mise en cache des commandes payées
│   ├── models.py               # Modèles de la base de données (peewee / PostgreSQL)
│   ├── payment.py              # Communication avec le service de paiement distant
│   ├── products.py             # Récupération des produits depuis le service distant
│   ├── routes.py               # Les routes de l'API REST
│   ├── tasks.py                 # Tâche de paiement exécutée en arrière-plan par le worker
│   └── test_app.py              # Tests automatiques
│
├── Dockerfile                  # Image Docker de l'application
├── docker-compose.yml          # Lance PostgreSQL 12 et Redis 5
├── requirements.txt            # Dépendances Python
├── run.py                      # Script d'orchestration pour le développement local
├── essai_async.py              # Script manuel : flux de paiement asynchrone (202 → polling → 200)
├── essaie_cache.py             # Script manuel : mise en cache d'une commande payée
├── essaie_cache_off.py         # Script manuel : lecture d'une commande depuis Redis sans PostgreSQL
├── essaie_cas.py               # Script manuel : conflit 409 et persistance d'une erreur de paiement
├── essais_multi.py             # Script manuel : création d'une commande multi-produits
├── CODE_ETUDIANT               # Codes permanents des membres de l'équipe
└── README.md
```

## Variables d'environnement

L'application est configurée par les variables d'environnement suivantes :

| Variable      | Description                       | Exemple                  |
|---------------|-----------------------------------|--------------------------|
| `FLASK_APP`   | Nom de l'application               | `api8inf349`             |
| `FLASK_DEBUG` | Mode debug                         | `True`                   |
| `DB_HOST`     | Hôte de connexion à PostgreSQL     | `localhost`              |
| `DB_USER`     | Nom d'usager de la base de données | `user`                   |
| `DB_PASSWORD` | Mot de passe de la base de données | `pass`                   |
| `DB_PORT`     | Port de connexion à PostgreSQL     | `5432`                   |
| `DB_NAME`     | Nom de la base de données          | `api8inf349`             |
| `REDIS_URL`   | URL de connexion à Redis           | `redis://localhost`      |

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

```powershell
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

- http://127.0.0.1:5000/test — page de test manuel (partie 1)

- http://127.0.0.1:5000/boutique — interface complète (partie 2) : consulter les
  produits, créer une commande avec un ou plusieurs produits, saisir l'adresse
  de livraison, payer et consulter une commande

## Lancement avec Docker

### Construire l'image

```
docker build -t api8inf349 .
```

### Lancer le conteneur

PostgreSQL et Redis doivent tourner (via `docker compose up -d`). Comme
l'application tourne dans un conteneur, on remplace `localhost` par
`host.docker.internal` pour joindre PostgreSQL et Redis, et on publie le port
5000 pour y accéder depuis l'hôte :

```
docker run -p 5000:5000 -e REDIS_URL=redis://host.docker.internal -e DB_HOST=host.docker.internal -e DB_USER=user -e DB_PASSWORD=pass -e DB_PORT=5432 -e DB_NAME=api8inf349 api8inf349
```

## Routes de l'API

| Méthode | Route          | Description                                    |
|---------|----------------|-------------------------------------------------|
| GET     | `/`            | Liste des produits                              |
| POST    | `/order`       | Créer une commande (un ou plusieurs produits)   |
| GET     | `/order/<id>`  | Consulter une commande                          |
| PUT     | `/order/<id>`  | Ajouter email + adresse, ou payer               |

## Fonctionnalités

- Création de commande avec un ou plusieurs produits
- Calcul automatique des taxes (par province) et des frais d'expédition
- Paiement par carte de crédit via un service distant
- Paiement traité en arrière-plan (RQ) : retourne `202` pendant le traitement,
  `409` si un paiement est déjà en cours
- Mise en cache des commandes payées dans Redis (consultables même sans
  PostgreSQL)
- Persistance des erreurs de paiement dans la transaction

## Lancer les tests

Des tests sont accessibles en web via : http://127.0.0.1:5000/test

Des tests peuvent aussi être lancés avec :

```
pytest test_app.py -v
```

Il y a 14 tests différents :
- test_liste_produits
- test_creer_commande_sans_produit
- test_creer_commande_quantite_invalide
- test_creer_commande_produit_en_rupture
- test_creer_commande_succes
- test_consulter_commande
- test_consulter_commande_inexistante
- test_put_information_client
- test_put_champ_manquant
- test_put_carte_et_infos_ensemble
- test_paiement_succes
- test_paiement_carte_refusee
- test_paiement_sans_adresse
- test_paiement_deja_payee

### Scripts de test manuel (partie 2)

Les fonctionnalités de la deuxième remise (multi-produits, cache, paiement
asynchrone) sont vérifiées avec des scripts manuels, à exécuter pendant que le
serveur et le worker roulent :

- **essai_async.py** : crée une commande, la paie, et vérifie le passage de 202
  (en cours) à 200 (terminée) après le traitement du worker
- **essaie_cache.py** : vérifie qu'une commande payée est bien mise en cache
  dans Redis
- **essaie_cache_off.py** : vérifie que la commande payée reste accessible via
  Redis même lorsque PostgreSQL est arrêté
- **essaie_cas.py** : vérifie le code 409 lors d'un second paiement pendant
  qu'un premier est en cours, ainsi que la persistance d'une erreur de carte
  refusée
- **essais_multi.py** : vérifie la création d'une commande avec plusieurs
  produits, ainsi que la rétrocompatibilité avec le format à un seul produit

## Le parcours complet

Le parcours complet se fait en plusieurs étapes de l'achat :

1. Charger les produits pour les afficher
2. Choisir un ou plusieurs produits (ID) et leur quantité
3. Créer la commande
4. Remplir l'adresse de livraison et la province (QC, ON, AB, BC ou NS)
5. Payer avec la carte (exemple : 4242 4242 4242 4242 — CVV 123 — expiration 09/2026)
6. Le paiement est traité en arrière-plan (code 202) ; consulter la commande
   jusqu'à l'obtention du code 200 pour voir le résultat (payée ou erreur de
   paiement)

## Nouveautés de la deuxième remise

- Migration de la base de données de SQLite vers PostgreSQL (peewee)
- Ajout de Redis pour la mise en cache des commandes payées et pour la file de
  tâches
- Commandes pouvant contenir plus d'un produit, avec rétrocompatibilité pour
  un seul produit
- Extraction du paiement dans une tâche en arrière-plan (RQ) : 202 pendant le
  traitement, 409 si on tente de modifier une commande en cours de paiement,
  200 une fois le traitement terminé (payée ou erreur persistée)
- Résilience : une commande payée reste consultable depuis le cache Redis
  même si PostgreSQL est indisponible
- Dockerfile et docker-compose.yml pour le déploiement de l'application et de
  ses dépendances (PostgreSQL 12, Redis 5)
- Nouvelle interface web (boutique.html) supportant la commande multi-produits
  et le suivi du paiement asynchrone
