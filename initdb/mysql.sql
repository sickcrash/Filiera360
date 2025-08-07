-- MySQL dump 10.13  Distrib 8.0.42, for Linux (aarch64)
--
-- Host: localhost    Database: filiera360
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `invite_token`
--

DROP TABLE IF EXISTS `invite_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invite_token` (
  `code` varchar(20) NOT NULL,
  `expires_at` datetime NOT NULL,
  `used` tinyint(1) DEFAULT '0',
  `used_by` varchar(255) DEFAULT NULL,
  `used_at` datetime DEFAULT NULL,
  PRIMARY KEY (`code`),
  KEY `used_by` (`used_by`),
  CONSTRAINT `invite_token_ibfk_1` FOREIGN KEY (`used_by`) REFERENCES `users` (`email`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `liked_products`
--

DROP TABLE IF EXISTS `liked_products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `liked_products` (
  `user_email` varchar(255) NOT NULL,
  `ID` varchar(255) NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`user_email`,`ID`),
  KEY `fk_liked_products_product` (`ID`),
  CONSTRAINT `fk_liked_products_product` FOREIGN KEY (`ID`) REFERENCES `models` (`id`) ON DELETE CASCADE,
  CONSTRAINT `liked_products_ibfk_1` FOREIGN KEY (`user_email`) REFERENCES `users` (`email`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `models`
--

DROP TABLE IF EXISTS `models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `models` (
  `id` varchar(50) NOT NULL,
  `stringa` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `otp_codes`
--

DROP TABLE IF EXISTS `otp_codes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `otp_codes` (
  `email` varchar(255) NOT NULL,
  `otp` int NOT NULL,
  `expiration` datetime NOT NULL,
  PRIMARY KEY (`email`),
  CONSTRAINT `otp_codes_ibfk_1` FOREIGN KEY (`email`) REFERENCES `users` (`email`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `searches`
--

DROP TABLE IF EXISTS `searches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `searches` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `user_email` varchar(255) NOT NULL,
  `product_id` varchar(255) NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `user_email` (`user_email`,`product_id`,`timestamp`),
  KEY `fk_searches_product` (`product_id`),
  CONSTRAINT `fk_searches_product` FOREIGN KEY (`product_id`) REFERENCES `models` (`id`) ON DELETE CASCADE,
  CONSTRAINT `searches_ibfk_1` FOREIGN KEY (`user_email`) REFERENCES `users` (`email`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=263 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_operators`
--

DROP TABLE IF EXISTS `user_operators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_operators` (
  `user_email` varchar(255) NOT NULL,
  `operator_email` varchar(255) NOT NULL,
  PRIMARY KEY (`user_email`,`operator_email`),
  KEY `operator_email` (`operator_email`),
  CONSTRAINT `user_operators_ibfk_1` FOREIGN KEY (`user_email`) REFERENCES `users` (`email`),
  CONSTRAINT `user_operators_ibfk_2` FOREIGN KEY (`operator_email`) REFERENCES `users` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `manufacturer` varchar(255) NOT NULL,
  `role_id` int DEFAULT NULL,
  PRIMARY KEY (`email`),
  KEY `fk_users_role_id` (`role_id`),
  CONSTRAINT `fk_users_role_id` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-24 17:29:45


-- Popola la tabella dei ruoli
INSERT INTO roles (name) VALUES
  ('user'),
  ('operator'),
  ('producer');

-- Crea utenti di test con password hashate
INSERT INTO users (email, password, manufacturer, role_id) VALUES
  ('producer@test.com', '$2b$12$4RMEd4AN9AxNgJ94yDpc/usjB9p3SdpA0bNi.sXPzi4kDgCSviqsO', 'TestProducer', (SELECT id FROM roles WHERE name = 'producer')),
  ('operator@test.com', '$2b$12$gpmQnwKYwtktVtF7dthX6.GPhlx1axX.don6QOeWf5IAbcYPCOrXC', 'OperatorInc', (SELECT id FROM roles WHERE name = 'operator')),
  ('user@test.com', '$2b$12$YrChbzJpMmjcTuegRpYkDOsLkH9GErK13V9YywqHPRiW8BjVkyTKK', 'UserInc', (SELECT id FROM roles WHERE name = 'user'));


-- Relazione producer ↔ operator
INSERT INTO user_operators (user_email, operator_email) VALUES
  ('producer@test.com', 'operator@test.com');

-- Token di invito
INSERT INTO invite_token (code, expires_at, used) VALUES
  ('INVITE123', DATE_ADD(NOW(), INTERVAL 1 DAY), 0);

-- Modello di test
INSERT INTO models (id, stringa) VALUES
  ('model123', 'modello 3D');

-- Like e ricerca
INSERT INTO liked_products (user_email, ID, timestamp) VALUES
  ('producer@test.com', 'model123', NOW());

INSERT INTO searches (user_email, product_id, timestamp) VALUES
  ('producer@test.com', 'model123', NOW());
