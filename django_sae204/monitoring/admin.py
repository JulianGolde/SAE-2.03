"""
Interface d'administration Django (accessible sur /admin/).

@admin.register(Modele) branche un modèle dans l'admin et permet de le
consulter / créer / modifier / supprimer (CRUD) sans écrire de code.
"""
from django.contrib import admin

from .models import Capteur, Donnee


@admin.register(Capteur)
class CapteurAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "piece", "emplacement")  # colonnes affichées dans la liste
    search_fields = ("id", "nom", "piece", "emplacement") # champs de la barre de recherche
    list_filter = ("piece",)                              # filtres latéraux (par pièce)
    ordering = ("piece", "nom")                           # tri par défaut


@admin.register(Donnee)
class DonneeAdmin(admin.ModelAdmin):
    list_display = ("id", "capteur", "date_mesure", "temperature", "etat")  # colonnes
    list_filter = ("capteur__piece", "capteur", "date_mesure")  # filtres (pièce, capteur, date)
    search_fields = ("capteur__id", "capteur__nom")      # recherche par id/nom de capteur
    date_hierarchy = "date_mesure"                       # navigation par dates en haut de page
    ordering = ("-date_mesure",)                         # plus récentes d'abord
    list_select_related = ("capteur",)                   # joint la table capteurs (perf.)
    list_per_page = 25                                   # pages courtes (pagination)
    show_full_result_count = False                       # évite un COUNT lent sur grosse table

    @admin.display(description="État")                   # ajoute une colonne calculée "État"
    def etat(self, obj):
        return obj.etat                                  # réutilise la propriété du modèle
