"""
Script de lancement complet du projet :
1. Démarre les conteneurs Docker (Postgres + Redis)
2. Attend que Postgres soit prêt à accepter des connexions
3. Définit les variables d'environnement
4. Initialise la base de données (création des tables + chargement des produits)
5. Lance le serveur Flask

Utilisation :
    python run.py
"""

import os
import subprocess
import time
import sys

# ----------------------------------------------------------------------
# 1. Variables d'environnement (doivent correspondre au docker-compose.yml)
# ----------------------------------------------------------------------
os.environ["DB_HOST"] = "localhost"
os.environ["DB_USER"] = "user"
os.environ["DB_PASSWORD"] = "password"
os.environ["DB_NAME"] = "api8inf349"
os.environ["DB_PORT"] = "5432"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["FLASK_APP"] = "api8inf349"

# Évite les soucis d'encodage des messages PostgreSQL sous Windows
os.environ["PGCLIENTENCODING"] = "UTF8"
os.environ.setdefault("LC_MESSAGES", "C")


def run(cmd, **kwargs):
    print(f"\n>>> {' '.join(cmd)}")
    return subprocess.run(cmd, **kwargs)


def install_requirements():
    if not os.path.exists("requirements.txt"):
        print("[INFO] Pas de requirements.txt trouvé, étape ignorée.")
        return

    result = run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    if result.returncode != 0:
        print("[ERREUR] Échec de l'installation des dépendances.")
        sys.exit(1)


def start_docker():
    result = run(["docker", "compose", "up", "-d"])
    if result.returncode != 0:
        print("[ERREUR] Impossible de démarrer Docker Compose. "
              "Vérifie que Docker Desktop est lancé.")
        sys.exit(1)


def wait_for_postgres(host="localhost", port=5432, user="user",
                       password="password", dbname="api8inf349",
                       timeout=30):
    """Attend que Postgres accepte les connexions avant de continuer."""
    import psycopg2

    print("\n>>> Attente de la disponibilité de PostgreSQL...")
    start = time.time()
    last_error = None

    while time.time() - start < timeout:
        try:
            conn = psycopg2.connect(
                host=host, port=port, user=user,
                password=password, dbname=dbname,
            )
            conn.close()
            print("[OK] PostgreSQL est prêt.")
            return
        except Exception as e:
            last_error = e
            time.sleep(1)

    print(f"[ERREUR] PostgreSQL n'a pas répondu après {timeout}s.")
    print(f"Dernière erreur : {last_error}")
    sys.exit(1)


def init_database():
    from api8inf349 import create_app, init_database as init_db

    app = create_app()
    with app.app_context():
        init_db(load=True)
    return app


def main():
    install_requirements()
    start_docker()
    wait_for_postgres()
    app = init_database()

    print("\n>>> Lancement du serveur Flask sur http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()