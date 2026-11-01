from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from inventaire.models import HistoriqueSuppression, Objet
from .models import Acces, Badge, Porte

MDP = 'Test-local-827!'


class AccesRfidTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.lecteur = User.objects.create_user('lecteur', password=MDP)
        self.admin = User.objects.create_user('chef', password=MDP, is_staff=True)
        self.objet = Objet.objects.create(nom='Serre A', emplacement='Salle N377')
        self.porte = Porte.objects.create(nom='Porte N377', objet=self.objet)
        self.autre_porte = Porte.objects.create(nom='Porte garage', objet=self.objet)
        self.badge = Badge.objects.create(uid='A35F129C', titulaire='Yannick')
        self.badge.portes.add(self.porte)

    def api(self, user=None):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + Token.objects.get_or_create(user=user or self.lecteur)[0].key)
        return client

    def passer(self, uid, porte=None, client=None):
        return (client or self.api()).post('/api/acces/', {'porte': (porte or self.porte).pk, 'uid': uid}, format='json')

    def test_badge_autorise(self):
        r = self.passer('a3 5f 12 9c')   # espaces et minuscules acceptés
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data['autorise'])
        self.assertEqual(r.data['ouvrir_secondes'], 5)
        acces = Acces.objects.get()
        self.assertEqual((acces.badge, acces.autorise, acces.lecteur), (self.badge, True, self.lecteur))

    def test_refus_journalises(self):
        cas = {
            'inconnu': ('DEADBEEF', None),
            'non autorisé': ('A35F129C', self.autre_porte),
        }
        for nom, (uid, porte) in cas.items():
            with self.subTest(nom):
                r = self.passer(uid, porte)
                self.assertEqual(r.status_code, 403)
                self.assertFalse(r.data['autorise'])
                self.assertIn('message', r.data)
        self.assertEqual(Acces.objects.filter(autorise=False).count(), 2)

    def test_badge_desactive_expire_et_salle_fermee(self):
        self.badge.actif = False
        self.badge.save()
        self.assertEqual(self.passer('A35F129C').status_code, 403)
        self.badge.actif = True
        self.badge.expiration = timezone.localdate() - timedelta(days=1)
        self.badge.save()
        self.assertIn('expiré', self.passer('A35F129C').data['message'])
        self.badge.expiration = None
        self.badge.save()
        self.objet.actif = False
        self.objet.save()
        self.assertIn('Salle fermée', self.passer('A35F129C').data['message'])
        self.assertEqual(Acces.objects.filter(autorise=True).count(), 0)

    def test_erreurs_http(self):
        self.assertEqual(self.passer('12-34').status_code, 400)          # UID mal formé
        self.assertEqual(self.passer('A35F12').status_code, 400)         # 3 octets
        r = self.api().post('/api/acces/', {'porte': 999999, 'uid': 'A35F129C'}, format='json')
        self.assertEqual(r.status_code, 404)
        r = APIClient().post('/api/acces/', {'porte': self.porte.pk, 'uid': 'A35F129C'}, format='json')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self.api().get('/api/acces/').status_code, 405)
        self.assertEqual(Acces.objects.count(), 0)                        # rien de journalisé

    def test_api_badges_reservee_admin_et_suppression_tracee(self):
        donnees = {'uid': '04 a2 3b 1c 5d 6e 80', 'titulaire': 'Ana', 'portes': [self.porte.pk]}
        self.assertEqual(self.api().post('/api/badges/', donnees, format='json').status_code, 403)
        admin = self.api(self.admin)
        r = admin.post('/api/badges/', donnees, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['uid'], '04A23B1C5D6E80')
        self.assertEqual(admin.post('/api/badges/', {'uid': 'XYZ', 'titulaire': 'B'}, format='json').status_code, 400)
        self.assertEqual(admin.post('/api/badges/', donnees, format='json').status_code, 400)   # doublon
        self.assertEqual(self.passer('04A23B1C5D6E80').status_code, 200)
        self.assertEqual(admin.delete(f"/api/badges/{r.data['id']}/").status_code, 204)
        trace = HistoriqueSuppression.objects.get(type_element='badges')
        self.assertEqual(trace.donnees['portes'], [self.porte.pk])
        self.assertEqual(self.passer('04A23B1C5D6E80').status_code, 403)   # badge supprimé = refusé
        self.assertEqual(Acces.objects.first().uid_lu, '04A23B1C5D6E80')     # le journal garde l'UID

    def test_pages_web(self):
        self.client.force_login(self.lecteur)
        self.assertEqual(self.client.get('/acces/').status_code, 200)
        self.assertEqual(self.client.get('/acces/gestion/badges/').status_code, 403)
        self.client.post('/acces/tester/', {'porte': self.porte.pk, 'uid': 'A35F129C'})
        self.assertTrue(Acces.objects.get().autorise)
        self.client.force_login(self.admin)
        for url in ['/acces/gestion/badges/', '/acces/gestion/portes/', '/acces/gestion/badges/ajouter/', '/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get('/acces/gestion/inconnu/').status_code, 404)
        # Porte avec historique : suppression refusée
        self.client.post(f'/acces/gestion/portes/{self.porte.pk}/supprimer/')
        self.assertTrue(Porte.objects.filter(pk=self.porte.pk).exists())
