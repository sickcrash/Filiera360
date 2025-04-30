DROP TABLE IF EXISTS models;
DROP TABLE IF EXISTS searches;
DROP TABLE IF EXISTS liked_products;
DROP TABLE IF EXISTS otp_codes;
DROP TABLE IF EXISTS invite_token;
DROP TABLE IF EXISTS users;

CREATE TABLE `users` (
  `email` VARCHAR(255) PRIMARY KEY NOT NULL,
  `manufacturer` VARCHAR(255),
  `password` VARCHAR(255) NOT NULL,
  `role` ENUM('admin', 'operator', 'producer', 'user') NOT NULL,
  `operators` TEXT
);

CREATE TABLE `otp_codes` (
  `email` VARCHAR(255) PRIMARY KEY,
  `otp` INT NOT NULL,
  `expiration` DATETIME NOT NULL
);

CREATE TABLE `liked_products` (
  `ID` INT PRIMARY KEY,
  `Name` VARCHAR(255),
  `Manufacturer` VARCHAR(255),
  `CreationDate` DATE,
  `timestamp` DATETIME,
  `user_email` VARCHAR(255)
);

CREATE TABLE `searches` (
  `ID` INT PRIMARY KEY,
  `product_id` INT,
  `user_email` VARCHAR(255),
  `timestamp` DATETIME
);

CREATE TABLE `invite_token` (
  `code` VARCHAR(20) PRIMARY KEY,
  `expires_at` DATETIME NOT NULL,
  `used` BOOLEAN DEFAULT false
);

CREATE TABLE `models` (
  `id` INT PRIMARY KEY,
  `user_email` VARCHAR(255),
  `stringa` TEXT NOT NULL
);

ALTER TABLE `otp_codes` ADD CONSTRAINT `fk_otp_user_email` FOREIGN KEY (`email`) REFERENCES `users` (`email`) ON DELETE CASCADE;

ALTER TABLE `liked_products` ADD CONSTRAINT `fk_liked_user_email` FOREIGN KEY (`user_email`) REFERENCES `users` (`email`) ON DELETE CASCADE;

ALTER TABLE `searches` ADD CONSTRAINT `fk_search_user_email` FOREIGN KEY (`user_email`) REFERENCES `users` (`email`) ON DELETE CASCADE;

ALTER TABLE `models` ADD CONSTRAINT `fk_models_user_email` FOREIGN KEY (`user_email`) REFERENCES `users` (`email`) ON DELETE SET NULL;
