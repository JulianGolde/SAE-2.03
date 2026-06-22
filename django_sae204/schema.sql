-- =========================================================
--  SAE 2.04 - Groupe RTGRP12
--  Schéma de la base de données MySQL (serveur Windows .131)
--  Version corrigée :
--   - les index pointaient vers une table "mesures" inexistante -> "donnees"
--   - colonne de date harmonisée en "date_mesure" (cohérent avec le code Django)
-- =========================================================

CREATE DATABASE IF NOT EXISTS sae204 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sae204;

CREATE TABLE IF NOT EXISTS capteurs (
    id          VARCHAR(32)  PRIMARY KEY,
    nom         VARCHAR(64)  UNIQUE NOT NULL,
    piece       VARCHAR(64)  NOT NULL,
    emplacement VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS donnees (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    id_capteur  VARCHAR(32) NOT NULL,
    date_mesure DATETIME    NOT NULL,
    temperature DOUBLE      NOT NULL,
    FOREIGN KEY (id_capteur) REFERENCES capteurs(id) ON DELETE CASCADE
);

CREATE INDEX idx_idcapteur ON donnees(id_capteur);
CREATE INDEX idx_datemesure ON donnees(date_mesure);

-- =========================================================
--  Utilisateur dédié au service Django (recommandé)
--  Adapter le mot de passe, puis :  FLUSH PRIVILEGES;
-- =========================================================
-- CREATE USER 'django'@'10.252.12.130' IDENTIFIED BY 'MotDePasseFort';
-- GRANT ALL PRIVILEGES ON sae204.* TO 'django'@'10.252.12.130';
-- FLUSH PRIVILEGES;
