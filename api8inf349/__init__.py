import os

import click
from flask import Flask, app, send_from_directory

from .models import DATABASE, Product, ALL_MODELS
from .products import fetch_products


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
        ).on_conflict(conflict_target=[Product.id], preserve=[Product.name, Product.description, Product.price, Product.in_stock, Product.weight, Product.image]).execute()
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

    @app.before_request
    def _db_connect():
        try:
            if DATABASE.is_closed():
                DATABASE.connect()
        except Exception:
            pass

    @app.teardown_request
    def _db_close(exc):
        try:    
            if not DATABASE.is_closed():
                DATABASE.close()
        except Exception:
            pass

    @app.cli.command("init-db")
    def init_db():
        init_database(load=True)
        click.echo("Base de données initialisée.")

    @app.route("/test")
    def test_page():
        return send_from_directory(app.static_folder, "test.html")
    
    @app.route("/boutique")
    def boutique_page():
        return send_from_directory(app.static_folder, "boutique.html")


    from .routes import bp
    app.register_blueprint(bp)

    return app
