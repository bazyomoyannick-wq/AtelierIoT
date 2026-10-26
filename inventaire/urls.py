from django.urls import path
from . import views

urlpatterns = [
    path('', views.tableau, name='tableau'),
    path('inscription/', views.inscription, name='inscription'),
    path('mesures/', views.mesures, name='mesures'),
    path('journal/', views.journal, name='journal'),
    path('suppressions/', views.suppressions, name='suppressions'),
    path('commande/<int:pk>/', views.commande, name='commande'),
    path('inventaire/<str:type_element>/', views.liste, name='liste'),
    path('inventaire/<str:type_element>/ajouter/', views.editer, name='ajouter'),
    path('inventaire/<str:type_element>/<int:pk>/', views.fiche, name='fiche'),
    path('inventaire/<str:type_element>/<int:pk>/modifier/', views.editer, name='modifier'),
    path('inventaire/<str:type_element>/<int:pk>/supprimer/', views.supprimer, name='supprimer'),
]
