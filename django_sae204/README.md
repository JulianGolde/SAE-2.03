# SAE 2.04 — Service Django de supervision des températures (Groupe RTGRP12)

Application web Django qui exploite les mesures de température collectées via MQTT
et stockées dans la base MySQL `sae204` (serveur Windows **10.252.12.131**).

## Fonctionnalités

- **Tableau de bord** : graphique de la température en fonction du temps (Chart.js),
  filtres par capteur et par plage de dates, seuils critiques affichés, statistiques
  (nombre de mesures, min/max/moyenne) et dernière mesure par capteur.
- **Logs critiques** : journal filtrable et paginé des mesures dépassant les seuils
  (haute ≥ 30 °C, basse ≤ 5 °C — configurable).
- **Export Excel** : fichier `.xlsx` avec les mesures (critiques surlignées),
  un **graphique courbe** et une feuille de **synthèse** (min/moy/max par capteur).
- **Import CSV** : téléversement d'un fichier CSV (séparateur `,` ou `;`, décimales
  `.` ou `,`, dates FR ou ISO), avec création automatique des capteurs manquants.
- **Admin Django** : gestion complète (CRUD) des capteurs et des mesures.

## Arborescence

```
django_sae204/
├── manage.py
├── requirements.txt
├── .env.example
├── schema.sql                 # schéma MySQL corrigé
├── exemple_mesures.csv        # fichier d'exemple pour tester l'import
├── sae204/                    # configuration du projet
│   ├── settings.py            # connexion MySQL, seuils, langue FR
│   ├── urls.py / wsgi.py / asgi.py
└── monitoring/                # application principale
    ├── models.py              # Capteur, Donnee (managed=False)
    ├── admin.py  views.py  urls.py  forms.py  utils.py
    ├── management/commands/seed_demo.py   # données de démo (SQLite)
    └── templates/monitoring/  # base, dashboard, logs, import_csv
```

## Installation

```bash
cd django_sae204
python -m venv venv
# Windows :  venv\Scripts\activate     |  Linux :  source venv/bin/activate
pip install -r requirements.txt
```

> Si l'installation de `mysqlclient` échoue sous Windows, le projet bascule
> automatiquement sur **PyMySQL**. Il suffit alors d'exécuter :
> `pip install pymysql`

## Configuration

1. Créer la base et les tables sur le serveur MySQL (.131) :
   ```bash
   mysql -u root -p < schema.sql
   ```
2. Copier `.env.example` en `.env` et renseigner les identifiants :
   ```
   DB_NAME=sae204
   DB_USER=collecte
   DB_PASSWORD=********
   DB_HOST=10.252.12.131
   DB_PORT=3306
   ```
3. Créer les tables internes de Django (sessions, comptes admin…) **sans toucher**
   aux tables `capteurs`/`donnees` (elles sont en `managed=False`, Django ne les
   créera donc pas) :
   ```bash
   python manage.py makemigrations monitoring   # migration "vide" (managed=False)
   python manage.py migrate
   python manage.py createsuperuser
   ```
4. Lancer le serveur :
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   Accès depuis un PC du réseau : `http://10.252.12.130:8000/`

## Démonstration sans MySQL (mode SQLite)

Pour tester l'application hors du réseau (jeu de données factice) :

```bash
# Windows :  set DB_ENGINE=sqlite   |  Linux :  export DB_ENGINE=sqlite
python manage.py makemigrations monitoring
python manage.py migrate
python manage.py seed_demo --jours 10 --reset
python manage.py runserver
```

## Réglage des seuils critiques

Dans `.env` :

```
TEMP_CRITICAL_HIGH=30
TEMP_CRITICAL_LOW=5
```

## Note de cohérence avec le collecteur MQTT

Le schéma officiel définit la colonne **`date_mesure`**. Le script MQTT fourni
insère dans une colonne `timestamp` : pour rester cohérent avec ce projet,
remplacer dans la requête d'insertion `timestamp` par `date_mesure` :

```sql
INSERT INTO donnees (id_capteur, date_mesure, temperature) VALUES (%s, %s, %s)
```
```
```

---
Projet réalisé dans le cadre de la SAE 2.04 — Groupe **RTGRP12** — réseau `10.252.12.0/24`.
