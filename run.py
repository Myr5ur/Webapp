"""
1. installation des requirements
2. démarage des conteneurs postgres et redis
3. initialisation de la bdd
4. lancement du worker
5. lancement de l'application flask
"""

import os
import subprocess
import sys
import time

# variable d'environnement
os.environ["DB_HOST"] = "localhost"
os.environ["DB_USER"] = "user"
os.environ["DB_PASSWORD"] = "pass"
os.environ["DB_NAME"] = "api8inf349"
os.environ["DB_PORT"] = "5432"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["FLASK_APP"] = "api8inf349"
os.environ["FLASK_DEBUG"] = "True"

# execution d'une commande systeme et attent qu'elle se termine
def run(cmd, **kwargs):
    print(f"\n>>> {' '.join(cmd)}")
    return subprocess.run(cmd, **kwargs)


# 1. installation des requirements
def install_requirements():
    if not os.path.exists("requirements.txt"):
        return

    result = run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    if result.returncode != 0:
        sys.exit(1)


#2. démarage des conteneurs
def reset_docker():
    run(["docker", "compose", "down", "-v"])


def start_docker():
    result = run(["docker", "compose", "up", "-d"])
    if result.returncode != 0:
        sys.exit(1)


def wait_for_postgres(host="localhost", port=5432, user="user",
                       password="pass", dbname="api8inf349",
                       timeout=30):
    import psycopg2
    start = time.time()
    last_error = None
    while time.time() - start < timeout:
        try:
            conn = psycopg2.connect(
                host=host, port=port, user=user,
                password=password, dbname=dbname,
            )
            conn.close()
            return
        except Exception as e:
            last_error = e
            time.sleep(1)
    sys.exit(1)

# 3. initialisation de la bdd - init-db
def init_database():
    from api8inf349 import create_app, init_database as init_db
    app = create_app()
    with app.app_context():
        init_db(load=True)
    return app

# Démarage du worker
def start_worker():
    return subprocess.Popen(["flask", "worker"])


def main():
    # si --reset est en arg, on repart d'une base vierge - utile pour les tests
    if "--reset" in sys.argv:
        reset_docker()
    install_requirements()
    start_docker()
    wait_for_postgres()
    app = init_database()

    worker_process = start_worker()

# on essaye de lancer l'application flask, et on s'assure que le worker est bien arrêté à la fin
    try:
        app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
    finally:
        print("\n>>> Arrêt du worker RQ...")
        worker_process.terminate()
        worker_process.wait()


if __name__ == "__main__":
    main()