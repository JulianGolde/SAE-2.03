from django.db import models

class Aeroport(models.Model):
    nom = models.CharField(max_length=150, verbose_name="Nom de l'aéroport")
    pays = models.CharField(max_length=100, verbose_name="Pays")

    def __str__(self):
        return f"{self.nom} ({self.pays})"

class Piste(models.Model):
    numero = models.CharField(max_length=20, verbose_name="Numéro de piste")
    aeroport = models.ForeignKey(Aeroport, on_delete=models.CASCADE, related_name="pistes")
    longueur = models.IntegerField(help_text="Longueur en mètres")

    def __str__(self):
        return f"Piste {self.numero} - {self.aeroport.nom} ({self.longueur}m)"

class Compagnie(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom de la compagnie")
    description = models.TextField(blank=True, null=True)
    pays_rattachement = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

class TypeAvion(models.Model):
    marque = models.CharField(max_length=100, verbose_name="Constructeur")
    modele = models.CharField(max_length=100, verbose_name="Modèle exact")
    description = models.TextField(blank=True, null=True)
    image = models.URLField(max_length=500, blank=True, null=True)
    longueur_piste_necessaire = models.IntegerField(help_text="Distance d'atterrissage minimale en mètres")

    def __str__(self):
        return f"{self.marque} {self.modele}"

class Avion(models.Model):
    nom = models.CharField(max_length=50, verbose_name="Immatriculation")
    compagnie = models.ForeignKey(Compagnie, on_delete=models.CASCADE, related_name="flotte")
    type_avion = models.ForeignKey(TypeAvion, on_delete=models.PROTECT, related_name="appareils")

    def __str__(self):
        return f"{self.nom} [{self.type_avion}]"

class Vol(models.Model):
    avion = models.ForeignKey(Avion, on_delete=models.CASCADE, related_name="vols")
    pilote = models.CharField(max_length=150, verbose_name="Nom du pilote")
    aeroport_depart = models.ForeignKey(Aeroport, on_delete=models.CASCADE, related_name="vols_depart")
    date_heure_depart = models.DateTimeField(verbose_name="Date/Heure de départ")
    aeroport_arrivee = models.ForeignKey(Aeroport, on_delete=models.CASCADE, related_name="vols_arrivee")
    date_heure_arrivee = models.DateTimeField(verbose_name="Date/Heure d'arrivée")

    def __str__(self):
        return f"Vol {self.id} : {self.aeroport_depart.nom} -> {self.aeroport_arrivee.nom}"