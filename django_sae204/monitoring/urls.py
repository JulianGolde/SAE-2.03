"""
Routes (URLs) de l'application monitoring.

Chaque path() associe une adresse à une fonction-vue de views.py.
Le 'name=' permet de référencer l'URL ailleurs sans écrire le chemin en dur
(ex. dans les templates : {% url 'monitoring:dashboard' %}).
"""
from django.urls import path     # path = définit une route
from . import views              # nos vues

app_name = "monitoring"          # "espace de noms" -> on écrit 'monitoring:dashboard'

urlpatterns = [
    path("", views.dashboard, name="dashboard"),            # /            -> page principale
    path("api/data/", views.api_data, name="api_data"),     # /api/data/   -> données JSON (auto-refresh)
    path("logs/", views.logs_critiques, name="logs"),       # /logs/       -> journal des alertes
    path("export/", views.export_excel, name="export_excel"),  # /export/  -> téléchargement Excel
    path("import/", views.import_csv, name="import_csv"),   # /import/     -> import CSV
]
