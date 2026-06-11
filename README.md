# SAÉ 2.03 - Application de Gestion de Trafic Aéroportuaire
**IUT de Colmar - Département Réseaux & Télécommunications** *Groupe RT132*

---

## Sommaire
1. [Architecture Technique & Modélisation Relationnelle](#1-architecture-technique--modélisation-relationnelle)
2. [Scripts SQL & Initialisation de la Base](#2-scripts-sql--initialisation-de-la-base)
3. [Organisation du Projet et Répartition des Rôles](#3-organisation-du-projet-et-répartition-des-rôles)
4. [Démonstration & Validation Fonctionnelle](#4-démonstration--validation-fonctionnelle)
5. [Environnement Technique](#5-environnement-technique)

---

## 1. Architecture Technique & Modélisation Relationnelle

### Architecture de Déploiement (Niveau Production)
Contrairement à un environnement de développement classique utilisant le serveur de test natif de Django, ce projet est déployé selon les standards de production afin de garantir la sécurité, la performance et l'isolation des composants :

* **Nginx (Reverse Proxy) :** Placé en front-end, il intercepte le trafic web public sur le port `80`. Il gère directement la livraison ultra-rapide des fichiers statiques (CSS, images) et agit comme un bouclier de sécurité (protection contre les requêtes malveillantes) avant de transmettre les requêtes dynamiques.
* **Gunicorn (Serveur d'Application WSGI) :** Reçoit le flux filtré par Nginx et exécute de manière optimisée le code Python/Django via plusieurs processus serveurs (*workers*).
* **MariaDB (Base de Données Relationnelle) :** Isolé sur le système, le serveur de base de données est sécurisé via un utilisateur dédié (`django_app`) appliquant le principe du moindre privilège.

### Schéma Relationnel (DBML)
La structure repose sur une décomposition stricte en tables relationnelles afin d'éviter toute redondance et de valider les règles métiers (notamment la contrainte de sécurité critique d'un espacement minimal de 10 minutes entre deux mouvements sur une même piste).

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
