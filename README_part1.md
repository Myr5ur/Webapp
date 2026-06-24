INF349 Projet de session — Première Partie

Équipe : Corentin Carvalho · Ahmed Boumaiza · Thomas Lempereur


Objectifs:

• Se familiariser avec le développement Web
• Développer une API REST
• Utiliser des services Web distants
• S'assurer de la résilience et de la performance d'une application Web
• Déployer une application Web


Structure du projet :

Web/
├── inf349/
│   ├── __init__.py       # Factory Flask, chargement des produits au démarrage
│   ├── models.py         # Modèles Peewee  tables de la base de données  (Product, Order, ShippingInformation, CreditCard, Transaction)
│   ├── routes.py         # Endpoints API REST et ce qu'elles font
│   ├── payment.py        # Communication avec le service de paiement distant
│   └── products.py       # Récupération des produits depuis le service distant
|
├── Static
│    └── test.hmtl         # Page de test manuel
└── test_app.py             # Test automatique




Installation:

Installer les dépendances
pip install flask peewee pytest pytest-flask




Lancement:

powershell
1. Initialiser la base de données
$env:FLASK_DEBUG="True"; $env:FLASK_APP="inf349"; flask init-db

2. Lancer le serveur
$env:FLASK_DEBUG="True"; $env:FLASK_APP="inf349"; flask run


Les produits en Json est accessible à http://127.0.0.1:5000

L'interface web est accessible à http://127.0.0.1:5000/test


Lancer les tests:

Des tests sont dans web via : http://127.0.0.1:5000/test

Des tests peuvent aussi lancer avec : pytest test_app.py -v

il y a 14 test different :
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



Le parcours complet se fait en plusieurs étapes de l'achat:

Charger les produits pour les afficher
Choisir la commande et voir son status (payé ou non)
Choisir un produit (ID) et la quantiter 
Remplir l'adresse de livraison et la province (QC, ON, AB, BC ou NS) (rempli automatiquement pour le test)
Payer avec la carte (exemple : 4242 4242 4242 4242 — CVV 123 — expiry 09/2026 ) (rempli automatiquement pour le test)

