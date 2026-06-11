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
```
## 2. Organisation du Projet et Répartition des Rôles

Le développement technique et l'administration des infrastructures de cette SAÉ sont répartis en trois pôles de compétences distincts. Le pôle d'ingénierie cœur centralise la logique métier et les mécanismes de sécurité algorithmiques requis.
Pôle A : Ingénierie Cœur Backend, Algorithmique Avancée & Cybersécurité (Responsable : Julian)

-    Développement du Modèle de Données : Transcription du schéma relationnel via l'ORM Django et interfaçage avec le serveur MySQL de production.

-    Algorithme de Gestion Dynamique des Pistes : Conception du module de vérification de compatibilité (longueur requise) et du moteur d'ordonnancement temporel (calcul des conflits sur des fenêtres d'utilisation de 10 minutes avec propositions d'horaires alternatifs).

-    Module d'Importation de Masse : Écriture du parseur de fichiers pour l'injection automatisée de plans de vols et gestion des exceptions de formatage.

-    Sécurisation Informatique (CE1.02, CE3.05) : Validation des mécanismes de protection natifs (anti-injection SQL, XSS, CSRF), supervision par journalisation des logs applicatifs et réalisation d'une simulation d'attaque contrôlée pour tester la résilience.

Pôle B : Interface Dynamique, Remplissage & Intégration Client (Responsable : Kara Lydia)

  -  Développement Front-End : Intégration des interfaces et maquettes sous forme de templates dynamiques Django.

  - Système de Formulaires CRUD : Création des vues et formulaires pour la saisie, modification et suppression des Avions, Pistes et Vols.

  - Module d'Affichage Client : Génération dynamique des fiches de vols au départ ou à destination d'un aéroport sur une période donnée.

  - Peuplement de Base (Seeding) : Initialisation et alimentation de la base de données avec des jeux de données réels et cohérents en amont du déploiement.

Pôle C : Administration Système, Déploiement & Gestion de Projet (Responsable : Yildiz Ali)

  - Virtualisation & Configuration OS (Linux) : Déploiement et maintenance d'une machine virtuelle Linux sous VirtualBox accueillant l'environnement applicatif (Python, PIP, packages Django).

  - Routage et Accessibilité Réseau : Configuration des ports réseau (redirection NAT / Port Forwarding) pour rendre l'application accessible depuis l'extérieur.

  - Sécurité Périmétrique : Configuration des règles de pare-feu et gestion fine des droits d'accès des utilisateurs système.

  -  Pilotage de Projet : Suivi et mise à jour des outils de planification collaborative (tableau Trello et diagramme de Gantt).

## 3. Environnement Technique et Outils Métiers

L'implémentation repose exclusivement sur des outils et frameworks open-source stables :

-    Framework Applicatif : Django (Python)

-    Système de Gestion de Base de Données : MySQL

-    Environnement de Virtualisation : Linux (Ubuntu/Debian) via Oracle VirtualBox

 -   Planification et Versioning : Gantt Project, Trello, et Git/GitHub

## 4. Livrables et Critères d'Évaluation

 -   Dépôt GitHub Mutualisé : Code source applicatif complet, scripts d'initialisation, diagramme Gantt et supports de présentation.

 -   Machine Virtuelle Opérationnelle : Image système configurée et sécurisée prête pour la mise en production.

 -   Dossier d'Architecture et Déploiement (2 à 5 pages) : Guide d'installation pas-à-pas, topologie réseau (NAT) et répartition détaillée des contributions individuelles.

  -  Fiche Portfolio Individuelle : Bilan rédigé en anglais justifiant l'acquisition des compétences spécifiques selon le pôle attribué.

 -   Soutenance Collective : Démo fonctionnelle de 5 minutes suivie de 10 minutes d'échange et de questions.
