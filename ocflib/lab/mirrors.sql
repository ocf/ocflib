---
--- documentation of `mirrors` table in ocfstats
--- other tables are defined in labstats/labstats/bin/init.py
---

CREATE TABLE `mirrors` (
  `date` date NOT NULL,
  `dist` varchar(30) NOT NULL,
  `up` bigint(20) NOT NULL,
  `down` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE VIEW `mirrors_public` AS
       SELECT * FROM `mirrors`;

GRANT SELECT ON `ocfstats`.`mirrors_public` TO 'anonymous'@'%';
