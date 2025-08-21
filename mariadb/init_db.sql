-- Création de la table 99_users si elle n'existe pas déjà
CREATE TABLE IF NOT EXISTS `99_users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `prenom` VARCHAR(100) NOT NULL,
    `nom` VARCHAR(100) NOT NULL,
    `pseudo` VARCHAR(100) NOT NULL,
    `sha_mdp` VARCHAR(255) NOT NULL,
    `is_chg_mdp` BOOLEAN NOT NULL DEFAULT FALSE,
    `date_chg_mdp` DATE NOT NULL DEFAULT CURRENT_DATE,
    `email` VARCHAR(100) NOT NULL,
    `telephone` VARCHAR(20) NOT NULL,
    `created_at` DATE NOT NULL DEFAULT CURRENT_DATE,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `debut` DATE NOT NULL DEFAULT CURRENT_DATE,
    `fin` DATE DEFAULT NULL,
    `nb_errors` INT NOT NULL DEFAULT 0,
    `is_locked` BOOLEAN NOT NULL DEFAULT FALSE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insertion de l'utilisateur administrateur
INSERT INTO `99_users` (
    `prenom`, `nom`, `pseudo`, `sha_mdp`, `is_chg_mdp`, `email`, `telephone`, `is_active`, `debut`, `nb_errors`, `is_locked`
) VALUES (
    'Admin', 'istrateur', 'admin', '$argon2id$v=19$m=65536,t=4,p=3$5MRAo5AnOW3LV9gR/jRNFg$uWgIeoC6ZpyBowO/aNLTA2nndXfeGkEnsY+nsfCEzTc', TRUE, 'admin@example.com', '0000000000', TRUE, CURRENT_DATE, 0, FALSE
)
ON DUPLICATE KEY UPDATE
    `sha_mdp` = VALUES(`sha_mdp`),
    `is_active` = VALUES(`is_active`),
    `nb_errors` = VALUES(`nb_errors`),
    `is_locked` = VALUES(`is_locked`);

-- Note : L'utilisateur devra modifier son mot de passe à la première utilisation.
