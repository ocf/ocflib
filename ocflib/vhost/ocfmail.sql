ALTER DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `addresses` (
  `address` varchar(190) NOT NULL,
  `password` varchar(255) DEFAULT NULL,
  `forward_to` text NOT NULL,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
      ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY(`address`)
) ENGINE=InnoDB;


DROP VIEW IF EXISTS `domains`;
CREATE VIEW `domains` AS
    SELECT
        DISTINCT substring_index(`addresses`.`address`, '@', -1) AS `domain`
    FROM `addresses`
    ORDER BY `domain`;
