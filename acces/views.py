from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from inventaire.services import supprimer_avec_historique
from inventaire.views import exiger_admin
from .forms import BadgeForm, PorteForm, TestBadgeForm
from .models import Acces, Badge, Porte
from .services import verifier_acces

GESTION = {'badges': (Badge, BadgeForm, 'Badges RFID'), 'portes': (Porte, PorteForm, 'Portes')}


@login_required
def journal(request):
    acces = Acces.objects.select_related('porte', 'badge')
    filtre = request.GET.get('filtre', '')
    if filtre == 'refuses':
        acces = acces.filter(autorise=False)
    elif filtre == 'autorises':
        acces = acces.filter(autorise=True)
    return render(request, 'acces/journal.html', {
        'page': Paginator(acces, 20).get_page(request.GET.get('page')), 'filtre': filtre,
    })


@login_required
def tester(request):
    """Simule un passage de badge depuis le navigateur (sans matériel)."""
    form = TestBadgeForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            acces = verifier_acces(form.cleaned_data['porte'], form.cleaned_data['uid'], request.user)
            if acces.autorise:
                messages.success(request, f'Accès autorisé — {acces.raison} Ouverture {acces.porte.duree_ouverture} s.')
            else:
                messages.error(request, f'Accès refusé — {acces.raison}')
            return redirect('acces-tester')
        messages.error(request, 'UID refusé : voir le détail sous le champ.')
    return render(request, 'acces/tester.html', {'form': form})


@login_required
def gestion_liste(request, type_element):
    exiger_admin(request.user)
    model, form_class, titre = GESTION[type_element]
    return render(request, 'acces/gestion_liste.html', {
        'elements': model.objects.all(), 'titre': titre, 'type_element': type_element,
    })


@login_required
def gestion_editer(request, type_element, pk=None):
    exiger_admin(request.user)
    model, form_class, titre = GESTION[type_element]
    element = get_object_or_404(model, pk=pk) if pk else None
    form = form_class(request.POST or None, instance=element)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Enregistrement réussi.')
            return redirect('acces-gestion', type_element=type_element)
        messages.error(request, 'Le formulaire contient des erreurs : corrigez les champs signalés.')
    return render(request, 'inventaire/formulaire.html', {
        'form': form, 'titre': ('Modifier : ' if element else 'Ajouter : ') + titre,
        'retour': f'/acces/gestion/{type_element}/',
    })


@login_required
def gestion_supprimer(request, type_element, pk):
    exiger_admin(request.user)
    model, form_class, titre = GESTION[type_element]
    element = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        try:
            supprimer_avec_historique(element, request.user)
        except ProtectedError:
            messages.error(request, 'Suppression refusée : un historique d’accès dépend de cette fiche.')
        else:
            messages.success(request, 'Fiche supprimée et ajoutée à l’historique des suppressions.')
        return redirect('acces-gestion', type_element=type_element)
    return render(request, 'acces/supprimer.html', {'element': element, 'type_element': type_element})
