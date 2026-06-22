"""Routage principal du projet SAE 2.04."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("monitoring.urls")),
]

# Personnalisation de l'en-tête de l'admin Django
admin.site.site_header = "SAE 2.04 - Administration RTGRP12"
admin.site.site_title = "SAE 2.04"
admin.site.index_title = "Gestion des capteurs et des mesures"
