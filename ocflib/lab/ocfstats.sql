---
--- Documentation of the ocfstats database schema
---

CREATE TABLE IF NOT EXISTS `session` (
    `id` int NOT NULL AUTO_INCREMENT,
    `host` varchar(255) NOT NULL,
    `user` varchar(16) NOT NULL,
    `start` datetime NOT NULL,
    `end` datetime DEFAULT NULL,
    `last_update` datetime,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `staff` (
    `user` varchar(16) NOT NULL,
    PRIMARY KEY (`user`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `opstaff` (
    `user` varchar(16) NOT NULL,
    PRIMARY KEY (`user`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `printer_pages` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `date` datetime NOT NULL,
    `printer` varchar(255) NOT NULL,
    `value` int(11) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `printer_toner` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `date` datetime NOT NULL,
    `printer` varchar(255) NOT NULL,
    `value` int(11) NOT NULL,
    `max` int(11) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `mirrors` (
    `date` date NOT NULL,
    `dist` varchar(30) NOT NULL,
    `up` bigint(20) NOT NULL,
    `down` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


DROP VIEW IF EXISTS session_duration;
CREATE VIEW `session_duration` AS
    SELECT *, timediff(`end`, `start`) AS `duration` FROM `session`;

DROP VIEW IF EXISTS session_duration_public;
CREATE VIEW `session_duration_public` AS
    SELECT `id`, `host`, `start`, `end`, `duration` FROM `session_duration`;

DROP VIEW IF EXISTS staff_session_duration_public;
CREATE VIEW `staff_session_duration_public` AS
    SELECT * FROM `session_duration` WHERE `user` IN (
        SELECT `user` FROM `staff`
    );

DROP VIEW IF EXISTS users_in_lab;
CREATE VIEW `users_in_lab` AS
    SELECT `user`, `host`, `start` FROM `session` WHERE `end` IS NULL;

DROP VIEW IF EXISTS users_in_lab_count_public;
CREATE VIEW `users_in_lab_count_public` AS
    SELECT COUNT(DISTINCT `user`) AS `count` FROM `users_in_lab`;

--- This relies on the semester_start function, which is defined in ocfprinting.sql
DROP VIEW IF EXISTS unique_users_in_lab_count_public;
CREATE VIEW `unique_users_in_lab_count_public` AS
    SELECT COUNT(DISTINCT `user`) AS `users` FROM `session`
        WHERE `start` >= `semester_start`(CURDATE());

DROP VIEW IF EXISTS staff_in_lab_public;
CREATE VIEW `staff_in_lab_public` AS
    SELECT * FROM `users_in_lab` WHERE `user` IN (
        SELECT `user` FROM `staff`
    );

DROP VIEW IF EXISTS desktops_in_use_public;
CREATE VIEW desktops_in_use_public AS
    SELECT `host` FROM `session_duration_public`
    WHERE `end` IS NULL;

DROP VIEW IF EXISTS printer_pages_public;
CREATE VIEW `printer_pages_public` AS
    SELECT `id`, `date`, `printer`, `value` FROM `printer_pages`;

DROP VIEW IF EXISTS printer_toner_public;
CREATE VIEW `printer_toner_public` AS
    SELECT `id`, `date`, `printer`, `value`, `max` FROM `printer_toner`;

DROP VIEW IF EXISTS daily_sessions_public;
CREATE VIEW `daily_sessions_public` AS
    SELECT
        COUNT(*) as logins,
            COUNT(DISTINCT `user`) as unique_logins,
            DATE(start) as date
        FROM `session`
        GROUP BY `date`
        ORDER BY `date` DESC;

DROP VIEW IF EXISTS mirrors_public;
CREATE VIEW `mirrors_public` AS
    SELECT * FROM `mirrors`;


GRANT SELECT ON `ocfstats`.`session_duration_public` TO 'anonymous'@'%';
GRANT SELECT ON `ocfstats`.`users_in_lab_count_public` TO 'anonymous'@'%';
GRANT SELECT ON `ocfstats`.`unique_users_in_lab_count_public` TO 'anonymous'@'%';
GRANT SELECT ON `ocfstats`.`staff_in_lab_public` TO 'anonymous'@'%';
GRANT SELECT ON `ocfstats`.`desktops_in_use_public` TO 'anonymous'@'%';
GRANT SELECT ON `ocfstats`.`staff_session_duration_public` TO 'anonymous'@'%';
GRANT SELECT ON `ocfstats`.`printer_pages_public` TO 'anonymous'@'%';
GRANT SELECT ON `ocfstats`.`printer_toner_public` TO 'anonymous'@'%';
GRANT SELECT ON `ocfstats`.`daily_sessions_public` TO 'anonymous'@'%';
GRANT SELECT ON `ocfstats`.`mirrors_public` TO 'anonymous'@'%';
