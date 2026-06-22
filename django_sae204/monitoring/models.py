"""
Modèles = description des tables de la base, sous forme de classes Python.

Ces tables existent DÉJÀ dans MySQL (créées par schema.sql et remplies par le
collecteur MQTT). C'est pourquoi on met `managed = False` : Django se contente
de LIRE/ÉCRIRE dedans, il ne les crée ni ne les modifie (pas de migration).
"""
from django.conf import settings        # pour lire les seuils critiques
from django.db import models             # classes de base de l'ORM Django


class Capteur(models.Model):
    """Un capteur de température. Correspond à la table SQL `capteurs`."""

    # Chaque attribut = une colonne. Le 1er argument texte est le libellé affiché dans l'admin.
    id = models.CharField("Identifiant", max_length=32, primary_key=True)  # clé primaire (ex. MAC)
    nom = models.CharField("Nom", max_length=64, unique=True)              # nom unique
    piece = models.CharField("Pièce", max_length=64)                      # ex. "sejour"
    emplacement = models.CharField("Emplacement", max_length=128)         # ex. "Mur Nord"

    class Meta:                           # Meta = options de configuration du modèle
        managed = False                  # Django ne gère PAS la création de la table
        db_table = "capteurs"            # nom EXACT de la table dans MySQL
        verbose_name = "Capteur"         # libellé singulier (admin)
        verbose_name_plural = "Capteurs" # libellé pluriel (admin)
        ordering = ["piece", "nom"]      # tri par défaut

    def __str__(self):                   # texte affiché pour représenter un capteur
        return f"{self.nom} ({self.piece})"

    @property                            # @property = s'utilise comme un attribut : capteur.derniere_mesure
    def derniere_mesure(self):
        """Retourne la mesure la plus récente de ce capteur (ou None s'il n'y en a pas)."""
        # self.mesures = toutes les mesures liées (voir related_name dans Donnee)
        return self.mesures.order_by("-date_mesure").first()


class Donnee(models.Model):
    """Une mesure de température. Correspond à la table SQL `donnees`."""

    id = models.AutoField(primary_key=True)   # entier auto-incrémenté (clé primaire)

    # Clé étrangère : relie chaque mesure à un capteur (colonne SQL `id_capteur`).
    capteur = models.ForeignKey(
        Capteur,
        # DO_NOTHING : c'est MySQL (FK ON DELETE CASCADE de schema.sql) qui supprime
        # les mesures liées. Django n'a donc pas à toutes les lister sur la page de
        # confirmation de suppression d'un capteur -> page courte et rapide.
        on_delete=models.DO_NOTHING,
        db_column="id_capteur",          # nom EXACT de la colonne dans MySQL
        related_name="mesures",          # permet d'écrire capteur.mesures.all()
        verbose_name="Capteur",
    )
    date_mesure = models.DateTimeField("Date de mesure")    # date + heure de la mesure
    temperature = models.FloatField("Température (°C)")      # nombre à virgule

    class Meta:
        managed = False
        db_table = "donnees"
        verbose_name = "Mesure"
        verbose_name_plural = "Mesures"
        ordering = ["-date_mesure"]      # de la plus récente à la plus ancienne
        indexes = [                      # index = accélèrent les recherches/filtres
            models.Index(fields=["capteur"]),
            models.Index(fields=["date_mesure"]),
        ]

    def __str__(self):
        # capteur_id = l'id du capteur lié, sans requête supplémentaire
        return f"{self.capteur_id} : {self.temperature} °C le {self.date_mesure}"

    @property
    def etat(self):
        """Renvoie l'état de la mesure selon les seuils définis dans settings.py."""
        if self.temperature >= settings.TEMP_CRITICAL_HIGH:  # trop chaud
            return "HAUTE"
        if self.temperature <= settings.TEMP_CRITICAL_LOW:   # trop froid
            return "BASSE"
        return "OK"                                          # dans la plage normale

    @property
    def est_critique(self):
        """True si la mesure est hors des seuils (HAUTE ou BASSE)."""
        return self.etat != "OK"
