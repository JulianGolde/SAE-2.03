# SAE-2.03

## Sommaire
* [1. Architecture et Modélisation Relationnelle](#1-architecture-et-modélisation-relationnelle)
* [2. Organisation du Projet et Répartition des Rôles](#2-organisation-du-projet-et-répartition-des-rôles)
* [3. Environnement Technique et Outils Métiers](#3-environnement-technique-et-outils-métiers)
* [4. Livrables et Critères d'Évaluation](#4-livrables-et-critères-dévaluation)

---

## 1. Architecture et Modélisation Relationnelle

Cette section présente la conception de notre base de données relationnelle MySQL, indispensable pour assurer l'intégrité des informations de trafic aérien et optimiser les requêtes de l'application web.

![Schéma Relationnel - Gestion de Trafic Aérien](https://github.com/user-attachments/assets/9f939b20-8e59-4508-b63b-5f9bfead2cd7)
*Figure 1 : Diagramme relationnel des entités du trafic aérien (généré via dbdiagram.io).*

### Analyse technique et choix de modélisation
La structure réseau et applicative repose sur une décomposition stricte en tables relationnelles afin d'éviter toute redondance d'information et de valider les règles métiers du cahier des charges :
* **Infrastructures géographiques (`aeroport` et `piste`)** : Un aéroport est caractérisé par son nom et son pays. Les pistes d'atterrissage y sont rattachées via une clé étrangère `aeroport_id` (relation 1 à N). La `longueur` de la piste est stockée ici pour être comparée dynamiquement, lors de la création d'un vol, avec la distance d'arrêt minimale requise par l'appareil.
* **Gestion de la flotte (`compagnie`, `type_avion`, `avion`)** : Pour optimiser l'espace et les performances, les caractéristiques constructeurs (`marque`, `modele`, `longueur_piste_necessaire`) sont isolées dans la table `type_avion`. La table `avion` représente les appareils physiques de la flotte (immatriculation unique) et lie chaque machine à sa `compagnie` propriétaire ainsi qu'à son profil technique (`type_avion_id`).
* **Planification des flux (`vol`)** : Table centrale du système. Un vol associe un avion et un pilote à un aéroport de départ et un aéroport d'arrivée à des coordonnées temporelles précises (`date_heure_depart`, `date_heure_arrivee`). En raison de la double relation vers la table `aeroport`, l'ORM Django nécessite des configurations spécifiques de clés inversées pour éviter les collisions de requêtes.

### Code source de conception (Syntaxe DBML)
```dbml
Table aeroport {
  id int [pk, increment]
  nom varchar
  pays varchar
}

Table piste {
  id int [pk, increment]
  numero varchar
  aeroport_id int
  longueur int
}

Table compagnie {
  id int [pk, increment]
  nom varchar
  description text
  pays_rattachement varchar
}

Table type_avion {
  id int [pk, increment]
  marque varchar
  modele varchar
  description text
  image varchar
  longueur_piste_necessaire int
}

Table avion {
  id int [pk, increment]
  nom varchar
  compagnie_id int
  type_avion_id int
}

Table vol {
  id int [pk, increment]
  avion_id int
  pilote varchar
  aeroport_depart_id int
  date_heure_depart datetime
  aeroport_arrivee_id int
  date_heure_arrivee datetime
}

Ref: piste.aeroport_id > aeroport.id
Ref: avion.compagnie_id > compagnie.id
Ref: avion.type_avion_id > type_avion.id
Ref: vol.avion_id > avion.id
Ref: vol.aeroport_depart_id > aeroport.id
Ref: vol.aeroport_arrivee_id > aeroport.id
