from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from datetime import timedelta
from .models import Aeroport, Piste, Compagnie, TypeAvion, Avion, Vol
from .forms import AeroportForm, PisteForm, CompagnieForm, TypeAvionForm, AvionForm, VolForm
import csv
from django.contrib import messages
from django.shortcuts import render, redirect
from datetime import datetime
from .forms import UploadFileForm

# --- PAGE D'ACCUEIL ---
class AccueilView(TemplateView):
    template_name = 'gestion_trafic/base.html'


# --- 1. CRUD AÉROPORTS ---
class AeroportListView(ListView):
    model = Aeroport
    template_name = 'gestion_trafic/aeroports/liste.html'
    context_object_name = 'aeroports'


class AeroportCreateView(CreateView):
    model = Aeroport
    form_class = AeroportForm
    template_name = 'gestion_trafic/aeroports/formulaire.html'
    success_url = reverse_lazy('liste_aeroports')


class AeroportUpdateView(UpdateView):
    model = Aeroport
    form_class = AeroportForm
    template_name = 'gestion_trafic/aeroports/formulaire.html'
    success_url = reverse_lazy('liste_aeroports')


class AeroportDeleteView(DeleteView):
    model = Aeroport
    template_name = 'gestion_trafic/aeroports/suppression.html'
    success_url = reverse_lazy('liste_aeroports')


# --- 2. CRUD PISTES ---
class PisteListView(ListView):
    model = Piste
    template_name = 'gestion_trafic/pistes/liste.html'
    context_object_name = 'pistes'


class PisteCreateView(CreateView):
    model = Piste
    form_class = PisteForm
    template_name = 'gestion_trafic/pistes/formulaire.html'
    success_url = reverse_lazy('liste_pistes')


class PisteUpdateView(UpdateView):
    model = Piste
    form_class = PisteForm
    template_name = 'gestion_trafic/pistes/formulaire.html'
    success_url = reverse_lazy('liste_pistes')


class PisteDeleteView(DeleteView):
    model = Piste
    template_name = 'gestion_trafic/pistes/suppression.html'
    success_url = reverse_lazy('liste_pistes')


# --- 3. CRUD COMPAGNIES ---
class CompagnieListView(ListView):
    model = Compagnie
    template_name = 'gestion_trafic/compagnies/liste.html'
    context_object_name = 'compagnies'


class CompagnieCreateView(CreateView):
    model = Compagnie
    form_class = CompagnieForm
    template_name = 'gestion_trafic/compagnies/formulaire.html'
    success_url = reverse_lazy('liste_compagnies')


class CompagnieUpdateView(UpdateView):
    model = Compagnie
    form_class = CompagnieForm
    template_name = 'gestion_trafic/compagnies/formulaire.html'
    success_url = reverse_lazy('liste_compagnies')


class CompagnieDeleteView(DeleteView):
    model = Compagnie
    template_name = 'gestion_trafic/compagnies/suppression.html'
    success_url = reverse_lazy('liste_compagnies')


# --- 4. CRUD TYPES D'AVIONS ---
class TypeAvionListView(ListView):
    model = TypeAvion
    template_name = 'gestion_trafic/types_avions/liste.html'
    context_object_name = 'types_avions'


class TypeAvionCreateView(CreateView):
    model = TypeAvion
    form_class = TypeAvionForm
    template_name = 'gestion_trafic/types_avions/formulaire.html'
    success_url = reverse_lazy('liste_types_avions')


class TypeAvionUpdateView(UpdateView):
    model = TypeAvion
    form_class = TypeAvionForm
    template_name = 'gestion_trafic/types_avions/formulaire.html'
    success_url = reverse_lazy('liste_types_avions')


class TypeAvionDeleteView(DeleteView):
    model = TypeAvion
    template_name = 'gestion_trafic/types_avions/suppression.html'
    success_url = reverse_lazy('liste_types_avions')


# --- 5. CRUD AVIONS ---
class AvionListView(ListView):
    model = Avion
    template_name = 'gestion_trafic/avions/liste.html'
    context_object_name = 'avions'


class AvionCreateView(CreateView):
    model = Avion
    form_class = AvionForm
    template_name = 'gestion_trafic/avions/formulaire.html'
    success_url = reverse_lazy('liste_avions')


class AvionUpdateView(UpdateView):
    model = Avion
    form_class = AvionForm
    template_name = 'gestion_trafic/avions/formulaire.html'
    success_url = reverse_lazy('liste_avions')


class AvionDeleteView(DeleteView):
    model = Avion
    template_name = 'gestion_trafic/avions/suppression.html'
    success_url = reverse_lazy('liste_avions')


# --- 6. CRUD VOLS & ALGORITHME DES PISTES ---
class VolListView(ListView):
    model = Vol
    template_name = 'gestion_trafic/vols/liste.html'
    context_object_name = 'vols'


# Fonction utilitaire algorithmique pour la gestion des pistes (Pôle A)
def verifier_creneau_piste(aeroport_arrivee, avion, heure_arrivee):
    longueur_req = avion.type_avion.longueur_piste_necessaire
    pistes_compatibles = Piste.objects.filter(aeroport=aeroport_arrivee, longueur__gte=longueur_req)

    if pistes_compatibles.count() == 0:
        return False, None, f"Aucune piste compatible à {aeroport_arrivee.nom} pour ce type d'appareil."

    horaire_test = heure_arrivee
    while True:
        vols_conflits = Vol.objects.filter(
            aeroport_arrivee=aeroport_arrivee,
            date_heure_arrivee__gt=horaire_test - timedelta(minutes=10),
            date_heure_arrivee__lt=horaire_test + timedelta(minutes=10)
        ).count()

        if vols_conflits < pistes_compatibles.count():
            return (horaire_test == heure_arrivee), horaire_test, None

        horaire_test += timedelta(minutes=10)


class VolCreateView(CreateView):
    model = Vol
    form_class = VolForm
    template_name = 'gestion_trafic/vols/formulaire.html'
    success_url = reverse_lazy('liste_vols')

    def form_valid(self, form):
        # On intercepte les données avant sauvegarde pour exécuter l'algorithme
        v = form.save(commit=False)
        libre, horaire, erreur = verifier_creneau_piste(v.aeroport_arrivee, v.avion, v.date_heure_arrivee)

        if erreur:
            form.add_error(None, erreur)
            return self.form_invalid(form)
        elif not libre:
            form.add_error(None, f"Piste occupée. Créneau alternatif calculé : {horaire.strftime('%H:%M')}")
            return self.form_invalid(form)
        return super().form_valid(form)


class VolUpdateView(UpdateView):
    model = Vol
    form_class = VolForm
    template_name = 'gestion_trafic/vols/formulaire.html'
    success_url = reverse_lazy('liste_vols')


class VolDeleteView(DeleteView):
    model = Vol
    template_name = 'gestion_trafic/vols/suppression.html'
    success_url = reverse_lazy('liste_vols')


def importer_vols(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            fichier = request.FILES['fichier_csv']
            # Lecture du fichier ligne par ligne
            lignes = fichier.read().decode('utf-8').splitlines()
            lecteur = csv.reader(lignes, delimiter=',')

            vols_ajoutes = 0
            erreurs = 0

            for row in lecteur:
                try:
                    # Extraction des données de la ligne CSV
                    avion = Avion.objects.get(id=int(row[0]))
                    pilote = row[1]
                    aero_dep = Aeroport.objects.get(id=int(row[2]))
                    date_dep = datetime.strptime(row[3].strip(), '%Y-%m-%d %H:%M')
                    aero_arr = Aeroport.objects.get(id=int(row[4]))
                    date_arr = datetime.strptime(row[5].strip(), '%Y-%m-%d %H:%M')

                    # On utilise l'algorithme des pistes qu'on a créé précédemment !
                    libre, horaire_final, erreur_physique = verifier_creneau_piste(aero_arr, avion, date_arr)

                    if erreur_physique:
                        erreurs += 1
                        continue  # Piste trop courte, on passe au vol suivant

                    # Sauvegarde du vol (avec l'horaire potentiellement corrigé par l'algo)
                    Vol.objects.create(
                        avion=avion, pilote=pilote, aeroport_depart=aero_dep,
                        date_heure_depart=date_dep, aeroport_arrivee=aero_arr,
                        date_heure_arrivee=horaire_final
                    )
                    vols_ajoutes += 1

                except Exception as e:
                    erreurs += 1  # Ligne mal formatée ou ID introuvable

            messages.success(request, f"Import terminé : {vols_ajoutes} vols ajoutés, {erreurs} erreurs ignorées.")
            return redirect('liste_vols')
    else:
        form = UploadFileForm()

    return render(request, 'gestion_trafic/vols/import.html', {'form': form})