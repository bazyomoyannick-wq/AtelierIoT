from django.urls import path, register_converter
from . import views


class TypeGestion:
    regex = 'badges|portes'

    def to_python(self, valeur):
        return valeur

    def to_url(self, valeur):
        return valeur


register_converter(TypeGestion, 'gestion')

urlpatterns = [
    path('', views.journal, name='acces-journal'),
    path('tester/', views.tester, name='acces-tester'),
    path('gestion/<gestion:type_element>/', views.gestion_liste, name='acces-gestion'),
    path('gestion/<gestion:type_element>/ajouter/', views.gestion_editer, name='acces-ajouter'),
    path('gestion/<gestion:type_element>/<int:pk>/modifier/', views.gestion_editer, name='acces-modifier'),
    path('gestion/<gestion:type_element>/<int:pk>/supprimer/', views.gestion_supprimer, name='acces-supprimer'),
]
