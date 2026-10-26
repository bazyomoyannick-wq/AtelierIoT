"""Capteur simulé : envoie des mesures à l'API locale (luminosité en lux ou distance en cm)."""
import argparse
import getpass
import json
import random
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PLAGES = {'luminosite': (0, 1000), 'distance': (2, 400)}

parser = argparse.ArgumentParser(description='Envoyer des mesures simulées à notre API locale.')
parser.add_argument('--capteur', type=int, required=True, help='identifiant du capteur')
parser.add_argument('--type', choices=PLAGES, default='luminosite', help='plage par défaut')
parser.add_argument('--minimum', type=float)
parser.add_argument('--maximum', type=float)
parser.add_argument('--nombre', type=int, default=10)
parser.add_argument('--delai', type=float, default=2, help='secondes entre deux envois')
args = parser.parse_args()
minimum = PLAGES[args.type][0] if args.minimum is None else args.minimum
maximum = PLAGES[args.type][1] if args.maximum is None else args.maximum
if minimum > maximum or not 1 <= args.nombre <= 100:
    parser.error('Minimum <= maximum; nombre compris entre 1 et 100.')
jeton = getpass.getpass('Collez le jeton API (saisie invisible) : ').strip()
reussies = 0
try:
    for numero in range(1, args.nombre + 1):
        valeur = round(random.uniform(minimum, maximum), 2)
        donnees = json.dumps({'capteur': args.capteur, 'valeur': valeur}).encode('utf-8')
        requete = Request('http://127.0.0.1:8000/api/mesures/', data=donnees, headers={
            'Authorization': 'Token ' + jeton, 'Content-Type': 'application/json',
        }, method='POST')
        try:
            with urlopen(requete, timeout=10) as reponse:
                mesure = json.load(reponse)
                alerte = ' ALERTE' if mesure.get('en_alerte') else ''
                print(f"{numero}/{args.nombre} : HTTP {reponse.status}, mesure {mesure['id']}, valeur {mesure['valeur']}{alerte}")
                reussies += 1
        except HTTPError as erreur:
            # Feedback : on affiche le code et le message JSON du serveur.
            corps = json.loads(erreur.read().decode('utf-8') or '{}')
            print(f"{numero}/{args.nombre} : HTTP {erreur.code} — {corps.get('message')} {corps.get('detail')}")
            if erreur.code in (401, 403, 404):
                raise SystemExit(1)
        if numero < args.nombre:
            time.sleep(args.delai)
except URLError:
    print('Connexion impossible. Démarrez runserver sur 127.0.0.1:8000.')
    raise SystemExit(1)
except KeyboardInterrupt:
    print('Simulation arrêtée.')
print(f'Bilan : {reussies}/{args.nombre} mesures acceptées.')
