"""
Formulaires de l'application.

Un Form Django décrit les champs d'un formulaire et valide automatiquement
les données envoyées par l'utilisateur.
"""
from django import forms


class CSVImportForm(forms.Form):
    """Formulaire d'import d'un fichier CSV de mesures."""

    # Champ "fichier" : un sélecteur de fichier limité aux .csv (côté navigateur)
    fichier = forms.FileField(
        label="Fichier CSV",
        help_text="Colonnes attendues : id_capteur, piece, date_mesure, temperature "
        "(séparateur , ou ; — décimales avec . ou ,).",
        # widget = l'apparence HTML du champ ; on ajoute les classes CSS Bootstrap
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"}),
    )
    # Case à cocher : créer les capteurs absents de la base lors de l'import
    creer_capteurs = forms.BooleanField(
        label="Créer automatiquement les capteurs absents de la base",
        required=False,        # facultatif (peut être décoché)
        initial=True,          # cochée par défaut
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean_fichier(self):
        """Validation personnalisée du champ 'fichier' (appelée automatiquement)."""
        f = self.cleaned_data["fichier"]                 # le fichier envoyé
        if not f.name.lower().endswith(".csv"):          # mauvaise extension
            raise forms.ValidationError("Le fichier doit avoir l'extension .csv")
        if f.size > 10 * 1024 * 1024:                    # > 10 Mo
            raise forms.ValidationError("Fichier trop volumineux (max 10 Mo).")
        return f                                          # on renvoie la valeur validée
