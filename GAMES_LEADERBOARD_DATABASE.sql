-- ========================================
-- GAMES & LEADERBOARD DATABASE SCHEMA
-- Run this in HeidiSQL/MariaDB
-- ========================================

-- 1. GAME table - List of available games
CREATE TABLE IF NOT EXISTS `GAME` (
    `game_id` INT AUTO_INCREMENT PRIMARY KEY,
    `game_name` VARCHAR(100) NOT NULL UNIQUE,
    `game_description` TEXT,
    `game_icon` VARCHAR(50) DEFAULT '🎮',
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. GAME_SCORE table - Store all game scores
CREATE TABLE IF NOT EXISTS `GAME_SCORE` (
    `score_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `game_id` INT NOT NULL,
    `score` INT NOT NULL,
    `level` INT DEFAULT 1,
    `time_played` INT DEFAULT 0, -- seconds
    `metadata` JSON, -- Store game-specific data (lines cleared, etc.)
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`game_id`) REFERENCES `GAME`(`game_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX `idx_game_score_user` (`user_id`, `game_id`, `score`),
    INDEX `idx_game_score_leaderboard` (`game_id`, `score` DESC, `created_at` DESC)
);

-- Insert available games
INSERT INTO `GAME` (`game_name`, `game_description`, `game_icon`) VALUES
('Flappy Bird', 'Enhanced Flappy Bird with clouds and better visuals!', '🐦'),
('Super Mario', 'Dodge flames and survive! Move up and down to avoid fireballs!', '👾')
ON DUPLICATE KEY UPDATE game_name = game_name;

-- Create view for leaderboard (top 100 per game)
DROP VIEW IF EXISTS `LEADERBOARD_VIEW`;
CREATE VIEW `LEADERBOARD_VIEW` AS
SELECT 
    gs.score_id,
    gs.user_id,
    u.username,
    gs.game_id,
    g.game_name,
    gs.score,
    gs.level,
    gs.time_played,
    gs.created_at,
    ROW_NUMBER() OVER (PARTITION BY gs.game_id ORDER BY gs.score DESC, gs.created_at ASC) as rank
FROM `GAME_SCORE` gs
JOIN `USER` u ON gs.user_id = u.user_id
JOIN `GAME` g ON gs.game_id = g.game_id
WHERE g.is_active = TRUE
ORDER BY gs.game_id, gs.score DESC, gs.created_at ASC;

