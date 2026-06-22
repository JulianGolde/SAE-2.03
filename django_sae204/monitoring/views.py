"""
Vues de l'application de supervision des températures.

Une "vue" (view) est une fonction qui reçoit une requête HTTP (request) et
renvoie une réponse HTTP (une page HTML, un JSON, un fichier...).
Les fonctions commençant par "_" sont des AIDES internes (pas des vues).
"""
# Outils de dates de la bibliothèque standard Python
from datetime import date, datetime, timedelta

# settings = accès aux réglages du projet (seuils, etc.) définis dans settings.py
from django.conf import settings
# messages = système pour afficher des messages flash (succès/erreur) à l'utilisateur
from django.contrib import messages
# Paginator = découpe une longue liste en pages
from django.core.paginator import Paginator
# cache = stockage temporaire (ici fichier) pour servir des données si la base tombe
from django.core.cache import cache
# Exceptions levées quand la base de données est injoignable ; transaction = bloc "tout ou rien"
from django.db import InterfaceError, OperationalError, transaction
# Fonctions d'agrégation SQL (moyenne, comptage, min, max) et Q (conditions OU/ET)
from django.db.models import Avg, Count, Max, Min, Q
# Réponses HTTP : HttpResponse (générique, ici pour le fichier Excel), JsonResponse (JSON)
from django.http import HttpResponse, JsonResponse
# render = fabrique une page HTML à partir d'un template ; redirect = renvoie vers une autre URL
from django.shortcuts import redirect, render

# Imports internes à notre application
from .forms import CSVImportForm          # le formulaire d'upload de CSV
from .models import Capteur, Donnee       # nos deux modèles (tables)
from .utils import build_workbook, parse_csv  # fonctions Excel et CSV

# Palette de couleurs : une couleur de courbe par capteur (réutilisée en boucle)
_PALETTE = [
    "#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed",
    "#0891b2", "#db2777", "#65a30d", "#ea580c", "#4f46e5",
]


def _parse_date(valeur, defaut):
    """Convertit une chaîne 'AAAA-MM-JJ' (envoyée par un <input type=date>) en objet date."""
    if not valeur:                 # champ vide ou absent
        return defaut              # -> on renvoie la valeur par défaut
    try:
        # strptime lit la chaîne selon le format, .date() ne garde que la date (pas l'heure)
        return datetime.strptime(valeur, "%Y-%m-%d").date()
    except ValueError:             # chaîne mal formée (ex. "abc")
        return defaut              # -> valeur par défaut plutôt que planter


def _lire_filtres(request):
    """Lit les filtres communs (capteur choisi + plage de dates) depuis l'URL (?capteur=...&debut=...)."""
    # request.GET = dictionnaire des paramètres après le "?" dans l'URL
    fin = _parse_date(request.GET.get("fin"), date.today())          # par défaut : aujourd'hui
    debut = _parse_date(request.GET.get("debut"), fin - timedelta(days=7))  # par défaut : 7 jours avant
    capteur_id = request.GET.get("capteur") or ""                    # "" = tous les capteurs
    return capteur_id, debut, fin   # on renvoie les trois valeurs d'un coup (tuple)


def _filtrer_mesures(capteur_id, debut, fin):
    """Construit la requête SQL des mesures comprises dans la plage de dates (et un capteur si choisi)."""
    # Donnee.objects = gestionnaire de requêtes ; select_related("capteur") = joint la table
    # capteurs en une seule requête (évite N requêtes supplémentaires).
    qs = Donnee.objects.select_related("capteur").filter(
        date_mesure__date__gte=debut,   # date_mesure (jour) >= debut
        date_mesure__date__lte=fin,     # et <= fin
    )
    if capteur_id:                       # si un capteur précis est demandé
        qs = qs.filter(capteur_id=capteur_id)  # on restreint à ce capteur
    return qs                            # qs = "QuerySet" (requête pas encore exécutée)


def _calcul_payload(capteur_id, debut, fin):
    """Calcule TOUTES les données du tableau de bord directement depuis la base."""
    # Mesures filtrées, triées par date croissante (pour tracer la courbe dans l'ordre)
    mesures = _filtrer_mesures(capteur_id, debut, fin).order_by("date_mesure")

    # --- 1) Construire une série de points par capteur (pour Chart.js) ---
    series = {}                          # dictionnaire { id_capteur : {nom, points[]} }
    for m in mesures:                    # on parcourt chaque mesure
        # setdefault : crée l'entrée du capteur si elle n'existe pas encore
        series.setdefault(m.capteur_id, {"nom": m.capteur.nom, "points": []})
        # on ajoute un point {x: date ISO, y: température} à la série de ce capteur
        series[m.capteur_id]["points"].append(
            {"x": m.date_mesure.strftime("%Y-%m-%dT%H:%M:%S"), "y": round(m.temperature, 2)}
        )

    # --- 2) Transformer ces séries en "datasets" au format attendu par Chart.js ---
    datasets = []
    for i, (cid, s) in enumerate(series.items()):  # enumerate donne un index i (pour la couleur)
        points = s["points"]
        if len(points) > 600:            # trop de points = graphique lent
            pas = len(points) // 600 + 1 # on calcule un "pas" d'échantillonnage
            points = points[::pas]       # on ne garde qu'un point sur "pas" (slicing)
        couleur = _PALETTE[i % len(_PALETTE)]  # % = modulo : recommence la palette si dépassée
        datasets.append(                 # un dataset = une courbe
            {
                "label": s["nom"],       # nom affiché dans la légende
                "data": points,          # les points {x, y}
                "borderColor": couleur,  # couleur de la ligne
                "backgroundColor": couleur,
                "borderWidth": 2,
                "pointRadius": 0,        # pas de gros points sur la courbe
                "tension": 0.25,         # léger lissage de la courbe
            }
        )

    # --- 3) Statistiques globales sur la période (une seule requête SQL via aggregate) ---
    agr = mesures.aggregate(
        n=Count("id"),                   # nombre de mesures
        tmin=Min("temperature"),         # température minimale
        tmax=Max("temperature"),         # température maximale
        tmoy=Avg("temperature"),         # température moyenne
    )
    # Nombre de mesures critiques : >= seuil haut OU <= seuil bas (Q permet le "OU" avec |)
    nb_critiques = mesures.filter(
        Q(temperature__gte=settings.TEMP_CRITICAL_HIGH)
        | Q(temperature__lte=settings.TEMP_CRITICAL_LOW)
    ).count()

    # --- 4) Dernière mesure de chaque capteur (état courant, peu importe la période choisie) ---
    dernieres = []
    for c in Capteur.objects.all():      # tous les capteurs
        # c.mesures = mesures liées à ce capteur (grâce au related_name) ; on prend la plus récente
        dm = c.mesures.order_by("-date_mesure").first()  # "-" = ordre décroissant ; first() = la 1re
        if dm:                           # si ce capteur a au moins une mesure
            dernieres.append(
                {
                    "piece": c.piece,
                    "nom": c.nom,
                    "temp": round(dm.temperature, 1),
                    "date": dm.date_mesure.strftime("%d/%m/%Y %H:%M"),
                    "etat": dm.etat,     # "HAUTE"/"BASSE"/"OK" (propriété du modèle)
                }
            )
    dernieres.sort(key=lambda d: d["piece"])  # tri par nom de pièce (lambda = mini-fonction)

    def arrondi(v):                      # petite aide locale : arrondit sauf si None
        return round(v, 1) if v is not None else None

    # On renvoie un dictionnaire unique rassemblant tout (sera converti en JSON / envoyé au template)
    return {
        "datasets": datasets,
        "seuilHaut": settings.TEMP_CRITICAL_HIGH,
        "seuilBas": settings.TEMP_CRITICAL_LOW,
        "stats": {
            "n": agr["n"] or 0,          # "or 0" : si None -> 0
            "tmin": arrondi(agr["tmin"]),
            "tmax": arrondi(agr["tmax"]),
            "tmoy": arrondi(agr["tmoy"]),
        },
        "nbCritiques": nb_critiques,
        "dernieres": dernieres,
    }


def _payload_vide():
    """Données "vides" renvoyées si la base est coupée ET que le cache est vide."""
    return {
        "datasets": [],
        "seuilHaut": settings.TEMP_CRITICAL_HIGH,
        "seuilBas": settings.TEMP_CRITICAL_LOW,
        "stats": {"n": 0, "tmin": None, "tmax": None, "tmoy": None},
        "nbCritiques": 0,
        "dernieres": [],
    }


def _payload_dashboard(capteur_id, debut, fin):
    """
    Version RÉSILIENTE de _calcul_payload :
      - si la base répond : calcule les données ET les met en cache ;
      - si la base est injoignable : ressort les dernières données connues (cache).
    Le drapeau 'horsLigne' indique au navigateur qu'on est en mode dégradé.
    """
    cle = f"dash:{capteur_id}:{debut}:{fin}"   # clé de cache unique par jeu de filtres
    try:
        payload = _calcul_payload(capteur_id, debut, fin)  # tentative normale (accès base)
        payload["horsLigne"] = False                       # base OK
        cache.set(cle, payload, 3600)                      # on mémorise 1h (3600 s)
        cache.set("dash:dernier", payload, 3600)           # filet de sécurité global
        return payload
    except (OperationalError, InterfaceError):             # base injoignable
        # on récupère le cache spécifique, sinon le dernier connu, sinon du vide
        secours = cache.get(cle) or cache.get("dash:dernier") or _payload_vide()
        secours = dict(secours)                            # copie (pour ne pas modifier le cache)
        secours["horsLigne"] = True                        # signale le mode hors-ligne
        return secours


def dashboard(request):
    """VUE : page principale (graphique température/temps + dernières mesures, auto-rafraîchie)."""
    capteur_id, debut, fin = _lire_filtres(request)   # lit les filtres de l'URL
    try:
        capteurs = list(Capteur.objects.all())        # liste pour le menu déroulant des filtres
    except (OperationalError, InterfaceError):
        capteurs = []                                 # base coupée : on garde la page accessible
    # contexte = données passées au template HTML
    contexte = {
        "capteurs": capteurs,
        "capteur_id": capteur_id,
        "debut": debut.isoformat(),                   # date au format texte 'AAAA-MM-JJ'
        "fin": fin.isoformat(),
        "payload": _payload_dashboard(capteur_id, debut, fin),  # données du graphique + stats
        "seuil_haut": settings.TEMP_CRITICAL_HIGH,
        "seuil_bas": settings.TEMP_CRITICAL_LOW,
    }
    # render = remplit le template avec le contexte et renvoie la page HTML
    return render(request, "monitoring/dashboard.html", contexte)


def api_data(request):
    """VUE : renvoie les données en JSON (appelée par le JavaScript toutes les 10 s)."""
    capteur_id, debut, fin = _lire_filtres(request)
    # JsonResponse transforme le dictionnaire Python en réponse JSON
    return JsonResponse(_payload_dashboard(capteur_id, debut, fin))


def logs_critiques(request):
    """VUE : journal paginé des mesures dépassant les seuils critiques."""
    capteur_id, debut, fin = _lire_filtres(request)
    type_alerte = request.GET.get("type") or ""       # "haute", "basse" ou "" (toutes)

    try:
        capteurs = list(Capteur.objects.all())
        # On garde uniquement les mesures critiques (>= seuil haut OU <= seuil bas)
        qs = _filtrer_mesures(capteur_id, debut, fin).filter(
            Q(temperature__gte=settings.TEMP_CRITICAL_HIGH)
            | Q(temperature__lte=settings.TEMP_CRITICAL_LOW)
        )
        if type_alerte == "haute":                    # filtre supplémentaire si demandé
            qs = qs.filter(temperature__gte=settings.TEMP_CRITICAL_HIGH)
        elif type_alerte == "basse":
            qs = qs.filter(temperature__lte=settings.TEMP_CRITICAL_LOW)

        # Pagination : 50 lignes par page, triées de la plus récente à la plus ancienne
        paginator = Paginator(qs.order_by("-date_mesure"), 50)
        page = paginator.get_page(request.GET.get("page"))  # page demandée (?page=2)
        total = paginator.count                        # nombre total d'alertes
        indisponible = False
    except (OperationalError, InterfaceError):         # base coupée : page accessible mais vide
        capteurs, page, total, indisponible = [], None, 0, True

    contexte = {
        "capteurs": capteurs,
        "capteur_id": capteur_id,
        "debut": debut.isoformat(),
        "fin": fin.isoformat(),
        "type_alerte": type_alerte,
        "page": page,                                  # objet page (mesures + infos pagination)
        "total": total,
        "indisponible": indisponible,
        "seuil_haut": settings.TEMP_CRITICAL_HIGH,
        "seuil_bas": settings.TEMP_CRITICAL_LOW,
    }
    return render(request, "monitoring/logs.html", contexte)


def export_excel(request):
    """VUE : génère et renvoie un fichier Excel (.xlsx) des mesures filtrées."""
    capteur_id, debut, fin = _lire_filtres(request)
    mesures = _filtrer_mesures(capteur_id, debut, fin).order_by("date_mesure")

    titre = "Températures"
    if capteur_id:                                     # si un capteur précis est filtré
        c = Capteur.objects.filter(pk=capteur_id).first()  # pk = clé primaire (l'id)
        if c:
            titre = f"Températures - {c.nom}"          # titre personnalisé du graphique Excel

    # build_workbook (dans utils.py) construit le classeur openpyxl
    wb = build_workbook(
        mesures, settings.TEMP_CRITICAL_HIGH, settings.TEMP_CRITICAL_LOW, titre=titre
    )

    nom_fichier = f"mesures_{debut.isoformat()}_{fin.isoformat()}.xlsx"
    # Réponse HTTP de type "fichier Excel"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    # En-tête qui force le téléchargement avec ce nom de fichier
    response["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'
    wb.save(response)                                  # openpyxl écrit le .xlsx dans la réponse
    return response


def import_csv(request):
    """VUE : importe des mesures depuis un fichier CSV téléversé."""
    if request.method == "POST":                       # POST = le formulaire a été soumis
        form = CSVImportForm(request.POST, request.FILES)  # on lit les données + le fichier
        if form.is_valid():                            # validations OK (extension, taille...)
            # parse_csv (utils.py) renvoie la liste des mesures + la liste des erreurs de lecture
            mesures, erreurs = parse_csv(form.cleaned_data["fichier"])
            creer = form.cleaned_data["creer_capteurs"]  # case "créer les capteurs manquants"

            # Ensemble des ids de capteurs déjà en base (pour savoir lesquels créer)
            capteurs_existants = set(Capteur.objects.values_list("id", flat=True))
            nouveaux_capteurs, a_inserer = {}, []      # à créer / mesures à insérer
            ignorees = list(erreurs)                   # on cumule les lignes ignorées

            for m in mesures:                          # pour chaque mesure lue dans le CSV
                cid = m["id_capteur"]
                # Capteur inconnu (ni en base, ni déjà prévu à la création) ?
                if cid not in capteurs_existants and cid not in nouveaux_capteurs:
                    if creer:                          # on a le droit de le créer
                        nouveaux_capteurs[cid] = Capteur(
                            id=cid, nom=m["nom"], piece=m["piece"], emplacement=m["emplacement"]
                        )
                    else:                              # création interdite -> on ignore la ligne
                        ignorees.append(f"Capteur inconnu « {cid} » (création désactivée).")
                        continue
                # Le capteur existe (ou va être créé) : on prépare l'insertion de la mesure
                if cid in capteurs_existants or cid in nouveaux_capteurs:
                    a_inserer.append(
                        Donnee(
                            capteur_id=cid,
                            date_mesure=m["date_mesure"],
                            temperature=m["temperature"],
                        )
                    )

            try:
                # transaction.atomic = tout réussit ou rien (pas d'insertion à moitié faite)
                with transaction.atomic():
                    if nouveaux_capteurs:
                        # bulk_create = insère plusieurs lignes en une fois (rapide)
                        Capteur.objects.bulk_create(list(nouveaux_capteurs.values()))
                    if a_inserer:
                        Donnee.objects.bulk_create(a_inserer, batch_size=500)
            except Exception as exc:                   # souci base -> message d'erreur
                messages.error(request, f"Erreur lors de l'insertion en base : {exc}")
                return redirect("monitoring:import_csv")

            # Message de succès (nombre de mesures et de capteurs créés)
            messages.success(
                request,
                f"{len(a_inserer)} mesure(s) importée(s), "
                f"{len(nouveaux_capteurs)} capteur(s) créé(s).",
            )
            if ignorees:                               # s'il y a eu des lignes ignorées, on prévient
                apercu = " | ".join(ignorees[:10])     # on n'affiche que les 10 premières
                suite = f" (+{len(ignorees) - 10} autre(s))" if len(ignorees) > 10 else ""
                messages.warning(request, f"{len(ignorees)} ligne(s) ignorée(s) : {apercu}{suite}")
            return redirect("monitoring:dashboard")    # retour au tableau de bord
    else:
        form = CSVImportForm()                         # GET = on affiche un formulaire vide

    return render(request, "monitoring/import_csv.html", {"form": form})
