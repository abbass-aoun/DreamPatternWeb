-- ========================================
-- DREAM COLLECTIONS DATABASE SCHEMA
-- Run this in HeidiSQL/MariaDB
-- ========================================

-- DREAM_COLLECTION table - User-created collections
CREATE TABLE IF NOT EXISTS `DREAM_COLLECTION` (
    `collection_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `collection_name` VARCHAR(100) NOT NULL,
    `description` TEXT,
    `color` VARCHAR(7) DEFAULT '#8a2be2',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- DREAM_COLLECTION_DREAM table - Many-to-many relationship
CREATE TABLE IF NOT EXISTS `DREAM_COLLECTION_DREAM` (
    `collection_id` INT NOT NULL,
    `dream_id` INT NOT NULL,
    `added_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`collection_id`, `dream_id`),
    FOREIGN KEY (`collection_id`) REFERENCES `DREAM_COLLECTION`(`collection_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`dream_id`) REFERENCES `DREAM`(`dream_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Index for better search performance
CREATE INDEX IF NOT EXISTS `idx_dream_search` ON `DREAM`(`user_id`, `dream_date`);
CREATE INDEX IF NOT EXISTS `idx_dream_text` ON `DREAM`(`user_id`, `dname`, `description`(255));




















