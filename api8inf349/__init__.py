import os
import click

from flask import Flask, send_from_directory
from rq import SimpleWorker
from .models import DATABASE, Product, ALL_MODELS
from .products import fetch_products
from .extensions import redis_conn, payment_queue


def load_products():
    products = fetch_products()
    for p in products:
        Product.insert(
            id=p["id"],
            name=p["name"].replace("\x00", ""),
            description=p.get("description", "").replace("\x00", ""),
            price=p["price"],
            in_stock=p["in_stock"],
            weight=p.get("weight", 0),
            image=p.get("image", "").replace("\x00", ""),
        ).on_conflict(
            conflict_target=[Product.id],
            preserve=[Product.name, Product.description, Product.price,
                      Product.in_stock, Product.weight, Product.image],
        ).execute()
    print(f"[INFO] {len(products)} produit(s) chargé(s).")


def init_database(load=True):
    DATABASE.connect(reuse_if_open=True)
    DATABASE.create_tables(ALL_MODELS)
    if load:
        load_products()
    if not DATABASE.is_closed():
        DATABASE.close()


def create_app(skip_product_load=False):
    app = Flask(__name__)

    @app.teardown_request
    def _db_close(exc):
        if not DATABASE.is_closed():
            DATABASE.close()

    @app.cli.command("init-db")
    def init_db():
        init_database(load=True)
        click.echo("Base de données initialisée.")

    @app.cli.command("worker")
    def worker_command():
       
        click.echo("Démarrage du worker RQ (queue 'payments')...")
        worker = SimpleWorker([payment_queue], connection=redis_conn)
        worker.work()

    @app.route("/test")
    def test_page():
        return send_from_directory(app.static_folder, "test.html")

    @app.route("/boutique")
    def boutique_page():
        return send_from_directory(app.static_folder, "boutique.html")

    if not skip_product_load and not os.environ.get("INF349_SKIP_LOAD"):
        init_database(load=True)

    from .routes import bp
    app.register_blueprint(bp)
    return app