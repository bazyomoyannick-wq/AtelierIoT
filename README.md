# Atelier IoT — Lumière et Distance

![Tests](https://github.com/bazyomoyannick-wq/AtelierIoT/actions/workflows/tests.yml/badge.svg)

Application web Django de supervision IoT : des capteurs de **luminosité** (photorésistance) et de **distance** (HC-SR04) envoient des mesures à une API REST, et des actionneurs (**lampe**, **barrière**) sont commandés depuis le site. Un **contrôle d'accès RFID** protège la salle de la serre. Projet du cours PROG1397 – Programmation côté serveur.

> Les mesures et les commandes sont simulées. Le lecteur RFID peut être simulé ou réel (Arduino Nano 33 IoT + RC522).

## Fonctionnalités

- **Tableau de bord** : dernière valeur de chaque capteur, alerte quand la valeur passe sous le seuil, accès refusés des dernières 24 h.
- **CRUD** complet : objets, capteurs, actionneurs (pages web et API).
- **Comptes et rôles** : un *utilisateur* consulte, ajoute, modifie et commande ; un *administrateur* peut aussi supprimer.
- **Historique des suppressions** : chaque suppression garde les données, l'auteur et la date.
- **Validation** côté navigateur (HTML + JavaScript) et côté serveur (modèles, formulaires, API).
- **Codes HTTP** clairs avec messages JSON : 200, 201, 204, 400, 401, 403, 404, 405.
- **Simulation** de capteurs et de badges par scripts Python ou par Postman.
- **Contrôle d'accès RFID** : badges, portes, journal des accès et API pour un lecteur RC522 (Nano 33 IoT).

## Technologies

Python 3.14 · Django 5.2 · Django REST framework · SQLite · Postman · Arduino (WiFiNINA, MFRC522)

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
| POST | `/api/acces/` | Passage de badge `{"porte": 1, "uid": "A35F129C"}` : 200 ouvrir, 403 refus |
| GET, POST | `/api/badges/`, `/api/portes/` | Gestion des badges et des portes (administrateur) |
| GET | `/api/journal-acces/` | Journal des passages de badges |

## Tests

    .\.venv\Scripts\python.exe manage.py test

- 21 tests automatiques Django, exécutés aussi par GitHub Actions à chaque `push`.
- Collection Postman `postman/AtelierIoT.postman_collection.json` : 48 requêtes, 80 vérifications.

## Simulation

    .\.venv\Scripts\python.exe manage.py drf_create_token votre_identifiant
    $env:JETON_API = "collez_ici_le_jeton"
    .\.venv\Scripts\python.exe simuler.py --capteur 1 --type luminosite --nombre 10
    .\.venv\Scripts\python.exe simuler_badge.py --porte 1 --uid A35F129C --uid DEADBEEF

## Lecteur RFID réel (facultatif)

1. Ouvrir `arduino/lecteur_rfid/lecteur_rfid.ino` dans l'IDE Arduino et installer WiFiNINA, ArduinoHttpClient, MFRC522 et Servo.
2. Copier `arduino_secrets.h.exemple` en `arduino_secrets.h` et le remplir (ce fichier n'est jamais publié).
3. Lancer le serveur sur le réseau local :

        $env:HOTES_SUPPLEMENTAIRES = "adresse_ip_du_pc"
        .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

## Structure

    config/        réglages et adresses du projet
    inventaire/    modèles, formulaires, vues, API, tests
    acces/         contrôle d'accès RFID (badges, portes, journal)
    templates/     pages HTML
    static/        feuille de style
    postman/       collection de tests Postman
    arduino/       croquis du lecteur RFID (Nano 33 IoT + RC522)
    simuler.py         capteur simulé
    simuler_badge.py   lecteur de badges simulé

## Auteur

Yannick Bazyomo — Programmation côté serveur (PROG1397)