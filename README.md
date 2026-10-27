# Atelier IoT — Lumière et Distance

![Tests](https://github.com/bazyomoyannick-wq/AtelierIoT/actions/workflows/tests.yml/badge.svg)

Application web Django de supervision IoT : des capteurs de **luminosité** (photorésistance) et de **distance** (HC-SR04) envoient des mesures à une API REST, et des actionneurs (**lampe**, **barrière**) sont commandés depuis le site. Projet du cours PROG1397 – Programmation côté serveur.

> Les mesures et les commandes sont simulées : aucun matériel réel n'est piloté.

## Fonctionnalités

- **Tableau de bord** : dernière valeur de chaque capteur, alerte quand la valeur passe sous le seuil.
- **CRUD** complet : objets, capteurs, actionneurs (pages web et API).
- **Comptes et rôles** : un *utilisateur* consulte, ajoute, modifie et commande ; un *administrateur* peut aussi supprimer.
- **Historique des suppressions** : chaque suppression garde les données, l'auteur et la date.
- **Validation** côté navigateur (HTML + JavaScript) et côté serveur (modèles, formulaires, API).
- **Codes HTTP** clairs avec messages JSON : 200, 201, 204, 400, 401, 403, 404, 405.
- **Simulation** de capteurs par script Python ou par Postman.

## Technologies

Python 3.14 · Django 5.2 · Django REST framework · SQLite · Postman

## Installation (Windows / PowerShell)

    py -3.14 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe manage.py migrate
    .\.venv\Scripts\python.exe manage.py createsuperuser
    .\.venv\Scripts\python.exe manage.py runserver

Ouvrir http://127.0.0.1:8000/

Données de démonstration (facultatif) :

    .\.venv\Scripts\python.exe manage.py loaddata donnees_demo.json

## API

Authentification par jeton : en-tête `Authorization: Token <jeton>`.

| Méthode | Adresse | Rôle |
|---|---|---|
| POST | `/api/inscription/` | Créer un compte utilisateur (renvoie un jeton) |
| POST | `/api/jeton/` | Obtenir le jeton d'un compte |
| GET, POST | `/api/objets/`, `/api/capteurs/`, `/api/actionneurs/` | Lister, créer |
| GET, PUT, PATCH | `/api/objets/<id>/` (idem capteurs, actionneurs) | Lire, modifier |
| DELETE | `/api/objets/<id>/` | Supprimer (administrateur) |
| GET, POST | `/api/mesures/?capteur=<id>` | Historique, nouvelle mesure |
| POST | `/api/actionneurs/<id>/commander/` | `{"etat": "on"}` ou `{"etat": "off"}` |
| GET | `/api/commandes/` | Journal des commandes |
| GET | `/api/suppressions/` | Historique des suppressions (administrateur) |

## Tests

    .\.venv\Scripts\python.exe manage.py test

- 15 tests automatiques Django, exécutés aussi par GitHub Actions à chaque `push`.
- Collection Postman `postman/AtelierIoT.postman_collection.json` : 32 requêtes, 51 vérifications.

## Simulation

    .\.venv\Scripts\python.exe manage.py drf_create_token votre_identifiant
    $env:JETON_API = "collez_ici_le_jeton"
    .\.venv\Scripts\python.exe simuler.py --capteur 1 --type luminosite --nombre 10

## Structure

    config/        réglages et adresses du projet
    inventaire/    modèles, formulaires, vues, API, tests
    templates/     pages HTML
    static/        feuille de style
    postman/       collection de tests Postman
    simuler.py     capteur simulé

## Auteur

Yannick Bazyomo — Programmation côté serveur (PROG1397)