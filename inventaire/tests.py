from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from .forms import MesureForm, CapteurForm
from .models import Objet, Capteur, Actionneur, Mesure, Commande, HistoriqueSuppression

MDP = 'Test-local-827!'


class ApplicationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('testeur', password=MDP)
        self.admin = User.objects.create_user('chef', password=MDP, is_staff=True)
        self.objet = Objet.objects.create(nom='Serre A', emplacement='Laboratoire')
        self.capteur = Capteur.objects.create(
            objet=self.objet, nom='Lumiere A', type_mesure='luminosite', seuil_alerte=300,
        )
        self.actionneur = Actionneur.objects.create(
            objet=self.objet, nom='Lampe A', type_action='lampe',
        )

    def api(self, user=None):
        client = APIClient()
        token = Token.objects.get_or_create(user=user or self.user)[0]
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        return client

    # ---------- Pages web ----------
    def test_visiteur_redirige(self):
        self.assertEqual(self.client.get('/').status_code, 302)
        self.assertEqual(self.client.get('/comptes/login/').status_code, 200)
        self.assertEqual(self.client.get('/inscription/').status_code, 200)

    def test_connexion_et_pages(self):
        self.assertTrue(self.client.login(username='testeur', password=MDP))
        urls = ['/', '/mesures/', '/journal/', '/inventaire/objets/',
                '/inventaire/capteurs/', '/inventaire/actionneurs/',
                '/inventaire/objets/ajouter/',
                f'/inventaire/objets/{self.objet.pk}/',
                f'/inventaire/capteurs/{self.capteur.pk}/',
                f'/inventaire/actionneurs/{self.actionneur.pk}/']
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get('/inventaire/inconnu/').status_code, 404)

    def test_inscription_web_cree_utilisateur(self):
        r = self.client.post('/inscription/', {
            'username': 'nouveau', 'password1': 'Serre-Lux-2026!', 'password2': 'Serre-Lux-2026!',
        })
        self.assertEqual(r.status_code, 302)
        self.assertFalse(get_user_model().objects.get(username='nouveau').is_staff)

    def test_crud_objet_admin_et_historique(self):
        self.client.force_login(self.admin)
        self.client.post('/inventaire/objets/ajouter/', {'nom': 'Bureau', 'emplacement': 'Local B', 'actif': 'on'})
        objet = Objet.objects.get(nom='Bureau')
        self.client.post(f'/inventaire/objets/{objet.pk}/modifier/', {
            'nom': 'Bureau', 'emplacement': 'Local C', 'actif': 'on'})
        objet.refresh_from_db()
        self.assertEqual(objet.emplacement, 'Local C')
        self.client.get(f'/inventaire/objets/{objet.pk}/supprimer/')
        self.assertTrue(Objet.objects.filter(pk=objet.pk).exists())
        self.client.post(f'/inventaire/objets/{objet.pk}/supprimer/')
        self.assertFalse(Objet.objects.filter(pk=objet.pk).exists())
        trace = HistoriqueSuppression.objects.get()
        self.assertEqual((trace.nom, trace.nom_utilisateur), ('Bureau', 'chef'))
        self.assertEqual(trace.donnees['emplacement'], 'Local C')
        # Objet protégé : refusé, et rien de plus dans l'historique.
        self.client.post(f'/inventaire/objets/{self.objet.pk}/supprimer/')
        self.assertTrue(Objet.objects.filter(pk=self.objet.pk).exists())
        self.assertEqual(HistoriqueSuppression.objects.count(), 1)

    def test_utilisateur_ne_peut_pas_supprimer(self):
        self.client.force_login(self.user)
        objet = Objet.objects.create(nom='Temp', emplacement='X')
        self.assertEqual(self.client.post(f'/inventaire/objets/{objet.pk}/supprimer/').status_code, 403)
        self.assertTrue(Objet.objects.filter(pk=objet.pk).exists())
        self.assertEqual(self.client.get('/suppressions/').status_code, 403)

    def test_mesure_valide_et_invalide(self):
        self.client.force_login(self.user)
        self.client.post('/mesures/', {'capteur': self.capteur.pk, 'valeur': '120.50'})
        self.assertEqual(Mesure.objects.get().valeur, Decimal('120.50'))
        self.assertContains(self.client.get('/'), 'ALERTE')  # 120 lux < seuil 300
        form = MesureForm(data={'capteur': self.capteur.pk, 'valeur': '20000'})
        self.assertFalse(form.is_valid())
        self.assertEqual(Mesure.objects.count(), 1)

    def test_historique_protege_type_capteur(self):
        Mesure.objects.create(capteur=self.capteur, valeur=500)
        form = CapteurForm(instance=self.capteur, data={
            'objet': self.objet.pk, 'nom': 'Lumiere A', 'type_mesure': 'distance', 'seuil_alerte': 20})
        self.assertFalse(form.is_valid())

    def test_commande_post_et_journal(self):
        self.client.force_login(self.user)
        url = f'/commande/{self.actionneur.pk}/'
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url, {'etat': 'on'})
        self.actionneur.refresh_from_db()
        self.assertTrue(self.actionneur.etat)
        self.assertEqual(Commande.objects.get().utilisateur, self.user)
        self.client.post(url, {'etat': 'off'})
        self.actionneur.refresh_from_db()
        self.assertFalse(self.actionneur.etat)
        self.assertEqual(Commande.objects.count(), 2)

    def test_objet_inactif(self):
        self.objet.actif = False
        self.objet.save()
        self.client.force_login(self.user)
        self.client.post(f'/commande/{self.actionneur.pk}/', {'etat': 'on'})
        self.assertEqual(Commande.objects.count(), 0)
        self.assertFalse(MesureForm(data={'capteur': self.capteur.pk, 'valeur': '25'}).is_valid())

    def test_csrf_exige(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(f'/commande/{self.actionneur.pk}/', {'etat': 'on'}).status_code, 403)
        self.assertEqual(Commande.objects.count(), 0)

    # ---------- API et codes HTTP ----------
    def test_api_inscription_et_jeton(self):
        r = APIClient().post('/api/inscription/', {'username': 'ana', 'password': 'Serre-Lux-2026!'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertIn('token', r.data)
        r = APIClient().post('/api/inscription/', {'username': 'ana', 'password': 'Serre-Lux-2026!'}, format='json')
        self.assertEqual(r.status_code, 400)
        r = APIClient().post('/api/jeton/', {'username': 'ana', 'password': 'mauvais'}, format='json')
        self.assertEqual(r.status_code, 400)
        r = APIClient().post('/api/jeton/', {'username': 'ana', 'password': 'Serre-Lux-2026!'}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_api_authentification_et_mesure(self):
        r = APIClient().get('/api/objets/')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.data['statut'], 401)
        api = self.api()
        self.assertEqual(api.get('/api/objets/').status_code, 200)
        r = api.post('/api/mesures/', {'capteur': self.capteur.pk, 'valeur': '823.25'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        r = api.post('/api/mesures/', {'capteur': self.capteur.pk, 'valeur': '-5'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Mesure.objects.count(), 1)
        self.assertEqual(api.delete(f'/api/mesures/{Mesure.objects.get().pk}/').status_code, 405)
        self.assertEqual(api.get('/api/objets/9999/').status_code, 404)

    def test_api_roles_suppression(self):
        r = self.api().post('/api/objets/', {'nom': 'B', 'emplacement': 'C'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        url = f"/api/objets/{r.data['donnees']['id']}/"
        self.assertEqual(self.api().patch(url, {'nom': 'C'}, format='json').status_code, 200)
        self.assertEqual(self.api().delete(url).status_code, 403)
        self.assertEqual(self.api().get('/api/suppressions/').status_code, 403)
        self.assertEqual(self.api(self.admin).delete(url).status_code, 204)
        self.assertEqual(self.api(self.admin).delete(f'/api/objets/{self.objet.pk}/').status_code, 400)
        r = self.api(self.admin).get('/api/suppressions/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)

    def test_api_commande(self):
        api = self.api()
        url = f'/api/actionneurs/{self.actionneur.pk}/commander/'
        self.assertEqual(api.get(url).status_code, 405)
        r = api.post(url, {'etat': 'on'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data['etat'])
        self.assertEqual(api.post(url, {'etat': 'peut-etre'}, format='json').status_code, 400)
        self.assertEqual(Commande.objects.count(), 1)

    def test_api_commande_objet_inactif(self):
        api = self.api()
        self.objet.actif = False
        self.objet.save()
        r = api.post(f'/api/actionneurs/{self.actionneur.pk}/commander/', {'etat': 'on'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Commande.objects.count(), 0)
