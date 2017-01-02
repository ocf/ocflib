--
-- This is kept here mostly to allow us to document the existing schema.
--

ALTER DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `jobs` (
    `id` int NOT NULL AUTO_INCREMENT,
    `user` varchar(255) NOT NULL,
    `time` datetime NOT NULL,
    `pages` int unsigned NOT NULL,
    `queue` varchar(255) NOT NULL,
    `printer` varchar(255) NOT NULL,
    `doc_name` varchar(510) NOT NULL,
    `filesize` int unsigned NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `refunds` (
    `id` int NOT NULL AUTO_INCREMENT,
    `user` varchar(255) NOT NULL,
    `time` datetime NOT NULL,
    `pages` int NOT NULL,
    `staffer` varchar(255) NOT NULL,
    `reason` varchar(510) NOT NULL,
    PRIMARY KEY(`id`)
) ENGINE=InnoDB;

CREATE INDEX `jobs_idx` ON `jobs` (`user`, `time`, `pages`);
CREATE INDEX `refunds_idx` ON `refunds` (`user`, `time`, `pages`);

DROP FUNCTION IF EXISTS semester_start;
DELIMITER $$
CREATE FUNCTION semester_start (d date) RETURNS date
        DETERMINISTIC
        BEGIN
        IF MONTH(d) >= 8 THEN
            RETURN MAKEDATE(YEAR(d), 213);  -- roughly august 1st
        ELSE
            RETURN MAKEDATE(YEAR(d), 1);
        END IF;
    END$$
DELIMITER ;

DROP VIEW IF EXISTS jobs_today;
CREATE VIEW jobs_today AS
    SELECT user, SUM(pages) AS pages
    FROM jobs
    WHERE DATE(jobs.time) = CURDATE()
    GROUP BY user;

DROP VIEW IF EXISTS refunds_today;
CREATE VIEW refunds_today AS
    SELECT user, SUM(pages) AS pages
    FROM refunds
    WHERE DATE(refunds.time) = CURDATE()
    GROUP BY user;

DROP VIEW IF EXISTS printed_today;
CREATE VIEW `printed_today` AS
    SELECT
        jobs_today.user AS user,
        COALESCE(jobs_today.pages, 0) - COALESCE(refunds_today.pages, 0) AS today
    FROM jobs_today
    LEFT OUTER JOIN refunds_today
    ON jobs_today.user = refunds_today.user
    GROUP BY jobs_today.user

    UNION

    SELECT
        refunds_today.user AS user,
        COALESCE(jobs_today.pages, 0) - COALESCE(refunds_today.pages, 0) AS today
    FROM jobs_today
    RIGHT OUTER JOIN refunds_today
    ON jobs_today.user = refunds_today.user
    GROUP BY refunds_today.user

    ORDER BY user;

DROP VIEW IF EXISTS jobs_semester;
CREATE VIEW jobs_semester AS
    SELECT user, SUM(pages) AS pages
    FROM jobs
    WHERE DATE(jobs.time) >= semester_start(CURDATE())
    GROUP BY user;

DROP VIEW IF EXISTS refunds_semester;
CREATE VIEW refunds_semester AS
    SELECT user, SUM(pages) AS pages
    FROM refunds
    WHERE DATE(refunds.time) >= semester_start(CURDATE())
    GROUP BY user;

DROP VIEW IF EXISTS printed_semester;
CREATE VIEW `printed_semester` AS
    SELECT
        jobs_semester.user AS user,
        COALESCE(jobs_semester.pages, 0) - COALESCE(refunds_semester.pages, 0) AS semester
    FROM jobs_semester
    LEFT OUTER JOIN refunds_semester
    ON jobs_semester.user = refunds_semester.user
    GROUP BY jobs_semester.user

    UNION

    SELECT
        refunds_semester.user AS user,
        COALESCE(jobs_semester.pages, 0) - COALESCE(refunds_semester.pages, 0) AS semester
    FROM jobs_semester
    RIGHT OUTER JOIN refunds_semester
    ON jobs_semester.user = refunds_semester.user
    GROUP BY refunds_semester.user

    ORDER BY user;

DROP VIEW IF EXISTS printed;
CREATE VIEW `printed` AS
    SELECT
        printed_semester.user AS user,
        COALESCE(printed_today.today, 0) AS today,
        COALESCE(printed_semester.semester, 0) AS semester
    FROM printed_today
    RIGHT OUTER JOIN printed_semester
    ON printed_today.user = printed_semester.user
    ORDER BY user;

GRANT SELECT ON `ocfprinting`.`printed` TO 'anonymous'@'%';
