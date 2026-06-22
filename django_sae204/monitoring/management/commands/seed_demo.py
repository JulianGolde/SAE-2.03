"""
Commande de démonstration : crée les tables (si besoin) et insère des mesures
factices, afin de tester le dashboard, les logs, l'export et l'import SANS MySQL.

Usage :
    DB_ENGINE=sqlite python manage.py seed_demo
    DB_ENGINE=sqlite python manage.py seed_demo --jours 14 --reset
"""
import math
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import connection

from monitoring.models import Capteur, Donnee

CAPTEURS_DEMO = [
    ("SAL01", "Capteur Salon", "Salon", "Mur Nord - VLAN 200"),
    ("SRV01", "Capteur Salle Serveur", "Salle Serveur", "Baie 1 - VLAN 300"),
    ("BUR01", "Capteur Bureau Admin", "Bureau Admin", "Plafond - VLAN 400"),
    ("EXT01", "Capteur Extérieur", "Extérieur", "Façade - VLAN 100"),
]

DDL = {
    "sqlite": [
        """CREATE TABLE IF NOT EXISTS capteurs (
            id VARCHAR(32) PRIMARY KEY,
            nom VARCHAR(64) UNIQUE NOT NULL,
            piece VARCHAR(64) NOT NULL,
            emplacement VARCHAR(128) NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS donnees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_capteur VARCHAR(32) NOT NULL,
            date_mesure DATETIME NOT NULL,
            temperature REAL NOT NULL,
            FOREIGN KEY (id_capteur) REFERENCES capteurs(id) ON DELETE CASCADE
        )""",
    ],
    "mysql": [
        """CREATE TABLE IF NOT EXISTS capteurs (
            id VARCHAR(32) PRIMARY KEY,
            nom VARCHAR(64) UNIQUE NOT NULL,
            piece VARCHAR(64) NOT NULL,
            emplacement VARCHAR(128) NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS donnees (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_capteur VARCHAR(32) NOT NULL,
            date_mesure DATETIME NOT NULL,
            temperature DOUBLE NOT NULL,
            FOREIGN KEY (id_capteur) REFERENCES capteurs(id) ON DELETE CASCADE
        )""",
    ],
}


class Command(BaseCommand):
    help = "Crée des données de démonstration (capteurs + mesures)."

    def add_arguments(self, parser):
        parser.add_argument("--jours", type=int, default=10, help="Nombre de jours d'historique.")
        parser.add_argument("--reset", action="store_true", help="Vide les tables avant insertion.")

    def handle(self, *args, **options):
        vendor = connection.vendor  # 'sqlite', 'mysql', ...
        ddl = DDL.get(vendor, DDL["mysql"])
        with connection.cursor() as cur:
            for stmt in ddl:
                cur.execute(stmt)
        self.stdout.write(self.style.SUCCESS(f"Tables vérifiées/créées (moteur : {vendor})."))

        if options["reset"]:
            Donnee.objects.all().delete()
            Capteur.objects.all().delete()
            self.stdout.write("Tables vidées.")

        for cid, nom, piece, emp in CAPTEURS_DEMO:
            Capteur.objects.update_or_create(
                id=cid, defaults={"nom": nom, "piece": piece, "emplacement": emp}
            )

        jours = options["jours"]
        debut = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(days=jours)
        bases = {"SAL01": 21.0, "SRV01": 26.0, "BUR01": 22.0, "EXT01": 14.0}

        mesures = []
        pas = timedelta(minutes=30)
        nb_pas = int(jours * 24 * 60 / 30)
        for cid, base in bases.items():
            for i in range(nb_pas):
                t = debut + i * pas
                # Cycle journalier (sinus sur 24h) + bruit
                heure = t.hour + t.minute / 60
                cycle = math.sin((heure - 6) / 24 * 2 * math.pi)
                temp = base + cycle * 3 + random.uniform(-0.6, 0.6)
                # Quelques pics critiques pour la salle serveur
                if cid == "SRV01" and random.random() < 0.01:
                    temp += random.uniform(6, 10)
                if cid == "EXT01" and 0 <= heure <= 5 and random.random() < 0.05:
                    temp -= random.uniform(8, 12)
                mesures.append(
                    Donnee(capteur_id=cid, date_mesure=t, temperature=round(temp, 2))
                )

        Donnee.objects.bulk_create(mesures, batch_size=1000)
        self.stdout.write(
            self.style.SUCCESS(
                f"{len(CAPTEURS_DEMO)} capteurs et {len(mesures)} mesures insérés "
                f"sur {jours} jours."
            )
        )
