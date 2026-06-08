from django import forms
from .models import Vol, Avion, TypeAvion, Compagnie, Piste, Aeroport

# --- FORMULAIRE VOL ---
class VolForm(forms.ModelForm):
    class Meta:
        model = Vol
        fields = ['avion', 'pilote', 'aeroport_depart', 'date_heure_depart', 'aeroport_arrivee', 'date_heure_arrivee']
        widgets = {
            'date_heure_depart': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'date_heure_arrivee': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

# --- FORMULAIRE AVION ---
class AvionForm(forms.ModelForm):
    class Meta:
        model = Avion
        fields = ['nom', 'compagnie', 'type_avion']
        # Django va automatiquement créer des menus déroulants pour 'compagnie' et 'type_avion'

# --- FORMULAIRE TYPE AVION ---
class TypeAvionForm(forms.ModelForm):
    class Meta:
        model = TypeAvion
        fields = ['marque', 'modele', 'description', 'image', 'longueur_piste_necessaire']

# --- FORMULAIRE COMPAGNIE ---
class CompagnieForm(forms.ModelForm):
    class Meta:
        model = Compagnie
        fields = ['nom', 'description', 'pays_rattachement']

# --- FORMULAIRE PISTE ---
class PisteForm(forms.ModelForm):
    class Meta:
        model = Piste
        fields = ['numero', 'aeroport', 'longueur']

# --- FORMULAIRE AEROPORT ---
class AeroportForm(forms.ModelForm):
    class Meta:
        model = Aeroport
        fields = ['nom', 'pays']

class UploadFileForm(forms.Form):
    fichier_csv = forms.FileField(
        label="Sélectionnez votre fichier CSV",
        help_text="Le fichier doit respecter la structure indiquée."
    )