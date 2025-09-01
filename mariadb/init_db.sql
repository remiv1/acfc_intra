-- Création de la table 99_users si elle n'existe pas déjà
CREATE TABLE IF NOT EXISTS `99_users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `prenom` VARCHAR(100) NOT NULL,
    `nom` VARCHAR(100) NOT NULL,
    `pseudo` VARCHAR(100) NOT NULL,
    `sha_mdp` VARCHAR(255) NOT NULL,
    `is_chg_mdp` BOOLEAN NOT NULL DEFAULT FALSE,
    `date_chg_mdp` DATE NOT NULL DEFAULT CURRENT_DATE,
    `permission` VARCHAR(10) NOT NULL DEFAULT '0',
    `email` VARCHAR(100) NOT NULL,
    `telephone` VARCHAR(20) NOT NULL,
    `created_at` DATE NOT NULL DEFAULT CURRENT_DATE,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `debut` DATE NOT NULL DEFAULT CURRENT_DATE,
    `fin` DATE DEFAULT NULL,
    `nb_errors` INT NOT NULL DEFAULT 0,
    `is_locked` BOOLEAN NOT NULL DEFAULT FALSE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TODO: Modifier le profil de l'admin (uniquement '1') en production
-- Insertion de l'utilisateur administrateur avec toutes les permissions (MODIFIER EN PROD)
INSERT INTO `99_users` (
    `prenom`, `nom`, `pseudo`, `sha_mdp`, `is_chg_mdp`, `email`, `telephone`, `is_active`, `permission`, `debut`, `nb_errors`, `is_locked`
) VALUES (
    'Admin', 'istrateur', 'admin', '$argon2id$v=19$m=65536,t=4,p=3$5MRAo5AnOW3LV9gR/jRNFg$uWgIeoC6ZpyBowO/aNLTA2nndXfeGkEnsY+nsfCEzTc', 1, 'admin@example.com', '0000000000', 1, '1234567', CURRENT_DATE, 0, 0
)
ON DUPLICATE KEY UPDATE
    `sha_mdp` = VALUES(`sha_mdp`),
    `is_active` = VALUES(`is_active`),
    `nb_errors` = VALUES(`nb_errors`),
    `is_locked` = VALUES(`is_locked`);

-- Note : L'utilisateur devra modifier son mot de passe à la première utilisation.

-- ========================================
-- DONNÉES DE RÉFÉRENCE
-- ========================================

-- Plan Comptable Général (PCG)
-- Source: prepare_base_datas/pcg/pcg.sql
CREATE TABLE IF NOT EXISTS 30_pcg (
    classe INT NOT NULL,
    categorie_1 INT NOT NULL,
    categorie_2 INT NOT NULL,
    compte INT PRIMARY KEY,
    denomination VARCHAR(255) NOT NULL
);

-- Indicatifs téléphoniques internationaux
-- Source: prepare_base_datas/indic_tel/92_indicatifs_tel.sql
CREATE TABLE IF NOT EXISTS 92_indicatifs_tel (
    id INT PRIMARY KEY,
    pays VARCHAR(255) NOT NULL,
    indicatif VARCHAR(6) NOT NULL
);

-- Villes françaises avec codes postaux
-- Source: prepare_base_datas/cp_villes/91_villes.sql
CREATE TABLE IF NOT EXISTS 91_villes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    code_postal INT NOT NULL
);

-- Catalogue de produits préformaté
-- Source: Transfert de données depuis ancienne base de données
CREATE TABLE IF NOT EXISTS 21_catalogue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type_produit VARCHAR(100) NOT NULL,
    stype_produit VARCHAR(100) NOT NULL,
    millesime INT NOT NULL,
    ref_auto VARCHAR(8),
    des_auto VARCHAR(100),
    prix_unitaire_ht DECIMAL(10,2) DEFAULT 0.00,
    geographie VARCHAR(10) GENERATED ALWAYS AS (UPPER(SUBSTRING_INDEX(SUBSTRING_INDEX(stype_produit, ' ', 4), ' ', -1))) STORED,
    poids VARCHAR(5) GENERATED ALWAYS AS (SUBSTRING_INDEX(SUBSTRING_INDEX(stype_produit, ' ', 3), ' ', -1)) STORED,
    created_at DATE DEFAULT (CURRENT_DATE) NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL
);

DELIMITER $$

CREATE TRIGGER trg_catalogue_before_insert
BEFORE INSERT ON 21_catalogue
FOR EACH ROW
BEGIN
    SET NEW.ref_auto = CONCAT(SUBSTRING(NEW.millesime, -2), UPPER(LEFT(NEW.type_produit, 4)), LPAD(NEW.id, 2, '0'));
    SET NEW.des_auto = CONCAT(UPPER(NEW.stype_produit), ' TARIF ', NEW.millesime);
END$$

DELIMITER ;

-- ========================================
-- INSERTION DES DONNÉES DE RÉFÉRENCE
-- ========================================

-- Insertion du Plan Comptable Général (PCG)
-- Note: Ce fichier contient plus de 580 comptes comptables
SOURCE docker-entrypoint-initdb.d/prepare_base_datas/pcg/pcg.sql;

-- Insertion des indicatifs téléphoniques internationaux
-- Note: Ce fichier contient les indicatifs de tous les pays
SOURCE docker-entrypoint-initdb.d/prepare_base_datas/indic_tel/92_indicatifs_tel.sql;

-- Insertion des villes françaises avec codes postaux
-- Note: Ce fichier contient plus de 33000 villes françaises
SOURCE docker-entrypoint-initdb.d/prepare_base_datas/cp_villes/91_villes.sql;

-- Insertion du catalogue de produits préformaté
-- Note: Ce fichier contient les données du catalogue
SOURCE docker-entrypoint-initdb.d/prepare_base_datas/catalogue/21_catalogue.sql;
