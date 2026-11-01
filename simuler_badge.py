"""Lecteur RFID simulé : présente un ou plusieurs badges à une porte via l'API locale.
Exemple : python simuler_badge.py --porte 1 --uid A35F129C --uid DEADBEEF"""
import argparse
import getpass
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser(description='Simuler le passage de badges RFID.')
parser.add_argument('--porte', type=int, required=True, help='identifiant de la porte')
parser.add_argument('--uid', action='append', required=True, help='UID du badge (répétable)')
parser.add_argument('--serveur', default='http://127.0.0.1:8000')
args = parser.parse_args()
# Le jeton du compte « lecteur » est lu dans JETON_API (jamais écrit dans le code).
jeton = os.environ.get('JETON_API', '').strip() or getpass.getpass('Collez le jeton API (saisie invisible) : ').strip()

for uid in args.uid:
    donnees = json.dumps({'porte': args.porte, 'uid': uid}).encode('utf-8')
    requete = Request(args.serveur + '/api/acces/', data=donnees, method='POST', headers={
        'Authorization': 'Token ' + jeton, 'Content-Type': 'application/json'})
    try:
        with urlopen(requete, timeout=10) as reponse:
            corps = json.load(reponse)
            print(f"{uid} : HTTP {reponse.status} — {corps['message']} (ouvrir {corps['ouvrir_secondes']} s)")
    except HTTPError as erreur:
        corps = json.loads(erreur.read().decode('utf-8') or '{}')
        print(f"{uid} : HTTP {erreur.code} — {corps.get('message')} {corps.get('detail', '')}")
        if erreur.code in (401, 404):
            raise SystemExit(1)
    except URLError:
        print('Connexion impossible. Démarrez runserver.')
        raise SystemExit(1)
