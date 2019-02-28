-- phpMyAdmin SQL Dump
-- version 4.8.2
-- https://www.phpmyadmin.net/
--
-- Host: mysql
-- Generation Time: Jan 30, 2019 at 12:14 AM
-- Server version: 10.1.37-MariaDB-0+deb9u1
-- PHP Version: 7.0.33-0+deb9u1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `ocfshorturls`
--

-- --------------------------------------------------------

--
-- Table structure for table `shorturls`
--

CREATE TABLE `shorturls` (
  `id` int(11) NOT NULL,
  `time_created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `slug` varchar(100) NOT NULL,
  `target` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Stand-in structure for view `shorturls_public`
-- (See below for the actual view)
--
CREATE TABLE `shorturls_public` (
`slug` varchar(100)
,`target` text
);

-- --------------------------------------------------------

--
-- Structure for view `shorturls_public`
--
DROP TABLE IF EXISTS `shorturls_public`;

CREATE ALGORITHM=UNDEFINED DEFINER=`ocfshorturls`@`%` SQL SECURITY DEFINER VIEW `shorturls_public`  AS  select `shorturls`.`slug` AS `slug`,`shorturls`.`target` AS `target` from `shorturls` ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `shorturls`
--
ALTER TABLE `shorturls`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `slug` (`slug`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `shorturls`
--
ALTER TABLE `shorturls`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
