-- ========================================
-- GAME SYSTEM DATABASE SCHEMA
-- Run this in HeidiSQL/MariaDB
-- ========================================

-- 1. USER_GAME_STATS table - Track XP, Level, Coins
CREATE TABLE IF NOT EXISTS `USER_GAME_STATS` (
    `stats_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `total_xp` INT DEFAULT 0,
    `current_level` INT DEFAULT 1,
    `dream_coins` INT DEFAULT 0,
    `total_coins_earned` INT DEFAULT 0,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY `unique_user_stats` (`user_id`)
);

-- 2. XP_TRANSACTION table - Track all XP gains
CREATE TABLE IF NOT EXISTS `XP_TRANSACTION` (
    `transaction_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `xp_amount` INT NOT NULL,
    `transaction_type` ENUM('DREAM_RECORDED', 'LUCID_DREAM', 'REALITY_CHECK', 'ACHIEVEMENT', 'BONUS') NOT NULL,
    `source_id` INT, -- dream_id, achievement_id, etc.
    `description` VARCHAR(255),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 3. COIN_TRANSACTION table - Track coin earnings and spending
CREATE TABLE IF NOT EXISTS `COIN_TRANSACTION` (
    `transaction_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `coin_amount` INT NOT NULL, -- positive for earned, negative for spent
    `transaction_type` ENUM('EARNED', 'SPENT', 'BONUS') NOT NULL,
    `source_id` INT,
    `description` VARCHAR(255),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 4. ACHIEVEMENT table - Game achievements
CREATE TABLE IF NOT EXISTS `ACHIEVEMENT` (
    `achievement_id` INT AUTO_INCREMENT PRIMARY KEY,
    `achievement_name` VARCHAR(100) NOT NULL,
    `achievement_description` TEXT,
    `achievement_icon` VARCHAR(50) DEFAULT '🏆',
    `requirement_type` ENUM('DREAM_COUNT', 'LUCID_COUNT', 'STREAK', 'INTENSITY', 'TIME', 'CUSTOM') NOT NULL,
    `requirement_value` INT NOT NULL,
    `xp_reward` INT DEFAULT 0,
    `coin_reward` INT DEFAULT 0,
    UNIQUE KEY `unique_achievement_name` (`achievement_name`)
);

-- 5. USER_ACHIEVEMENT table - Track user achievements
CREATE TABLE IF NOT EXISTS `USER_ACHIEVEMENT` (
    `user_achievement_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `achievement_id` INT NOT NULL,
    `earned_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`achievement_id`) REFERENCES `ACHIEVEMENT`(`achievement_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY `unique_user_achievement` (`user_id`, `achievement_id`)
);

-- 6. DREAM_STREAK table - Track consecutive days
CREATE TABLE IF NOT EXISTS `DREAM_STREAK` (
    `streak_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `current_streak` INT DEFAULT 0,
    `longest_streak` INT DEFAULT 0,
    `last_dream_date` DATE,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY `unique_user_streak` (`user_id`)
);

-- 7. REALITY_CHECK table - Track reality checks
CREATE TABLE IF NOT EXISTS `REALITY_CHECK` (
    `check_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `check_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `notes` TEXT,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 8. DREAM_SHOP table - Items available for purchase
CREATE TABLE IF NOT EXISTS `DREAM_SHOP` (
    `item_id` INT AUTO_INCREMENT PRIMARY KEY,
    `item_name` VARCHAR(100) NOT NULL,
    `item_description` TEXT,
    `item_icon` VARCHAR(50),
    `coin_cost` INT NOT NULL,
    `item_type` ENUM('THEME', 'BADGE', 'AVATAR', 'FEATURE', 'BONUS') NOT NULL,
    `is_active` BOOLEAN DEFAULT TRUE,
    UNIQUE KEY `unique_item_name` (`item_name`)
);

-- 9. USER_SHOP_PURCHASE table - Track purchases
CREATE TABLE IF NOT EXISTS `USER_SHOP_PURCHASE` (
    `purchase_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `item_id` INT NOT NULL,
    `purchased_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`item_id`) REFERENCES `DREAM_SHOP`(`item_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Insert 8 Achievements
INSERT INTO `ACHIEVEMENT` (`achievement_name`, `achievement_description`, `achievement_icon`, `requirement_type`, `requirement_value`, `xp_reward`, `coin_reward`) VALUES
('First Dream', 'Recorded your first dream', '🌙', 'DREAM_COUNT', 1, 10, 5),
('Dream Chronicler', 'Recorded 10 dreams', '📖', 'DREAM_COUNT', 10, 50, 25),
('Dream Master', 'Recorded 50 dreams', '🏆', 'DREAM_COUNT', 50, 200, 100),
('7-Day Streak', '7 consecutive days of recording', '🔥', 'STREAK', 7, 100, 50),
('Lucid Dreamer', 'Had your first lucid dream', '✨', 'LUCID_COUNT', 1, 50, 25),
('Reality Bender', 'Had 5 lucid dreams', '🌀', 'LUCID_COUNT', 5, 250, 125),
('Vivid Visionary', 'Recorded a dream with intensity 10', '💫', 'INTENSITY', 10, 75, 40),
('Early Bird', 'Recorded a dream before 7 AM', '🌅', 'TIME', 1, 30, 15)
ON DUPLICATE KEY UPDATE achievement_name = achievement_name;

-- Insert Shop Items
INSERT INTO `DREAM_SHOP` (`item_name`, `item_description`, `item_icon`, `coin_cost`, `item_type`) VALUES
('Premium Theme Pack', 'Unlock exclusive dream journal themes', '🎨', 100, 'THEME'),
('Golden Badge', 'Show off your dedication with a golden badge', '⭐', 200, 'BADGE'),
('Night Owl Avatar', 'Special avatar for night dreamers', '🦉', 150, 'AVATAR'),
('Extended Analysis', 'Get longer AI dream analyses', '📊', 300, 'FEATURE'),
('XP Boost', 'Double XP for your next 5 dreams', '⚡', 250, 'BONUS'),
('Streak Protector', 'Protect your streak from breaking once', '🛡️', 500, 'BONUS')
ON DUPLICATE KEY UPDATE item_name = item_name;

-- Create indexes
CREATE INDEX `idx_xp_transaction_user` ON `XP_TRANSACTION`(`user_id`, `created_at`);
CREATE INDEX `idx_coin_transaction_user` ON `COIN_TRANSACTION`(`user_id`, `created_at`);
CREATE INDEX `idx_streak_user` ON `DREAM_STREAK`(`user_id`);
CREATE INDEX `idx_reality_check_user` ON `REALITY_CHECK`(`user_id`, `check_date`);

-- ========================================
-- DATABASE TRIGGERS FOR AUTO XP CALCULATION
-- ========================================

-- Trigger 1: Award XP when dream is recorded
DROP TRIGGER IF EXISTS `award_xp_on_dream`;
DELIMITER //
CREATE TRIGGER `award_xp_on_dream`
AFTER INSERT ON `DREAM`
FOR EACH ROW
BEGIN
    DECLARE xp_gained INT DEFAULT 10;
    DECLARE coins_gained INT DEFAULT 1;
    DECLARE current_xp INT;
    DECLARE new_level INT;
    
    -- Base XP for recording dream
    INSERT INTO `XP_TRANSACTION` (`user_id`, `xp_amount`, `transaction_type`, `source_id`, `description`)
    VALUES (NEW.user_id, xp_gained, 'DREAM_RECORDED', NEW.dream_id, CONCAT('Recorded dream: ', NEW.dname));
    
    -- Award coins (1 coin per 10 XP)
    SET coins_gained = FLOOR(xp_gained / 10);
    INSERT INTO `COIN_TRANSACTION` (`user_id`, `coin_amount`, `transaction_type`, `source_id`, `description`)
    VALUES (NEW.user_id, coins_gained, 'EARNED', NEW.dream_id, 'XP reward');
    
    -- Update user stats
    INSERT INTO `USER_GAME_STATS` (`user_id`, `total_xp`, `dream_coins`, `total_coins_earned`)
    VALUES (NEW.user_id, xp_gained, coins_gained, coins_gained)
    ON DUPLICATE KEY UPDATE
        `total_xp` = `total_xp` + xp_gained,
        `dream_coins` = `dream_coins` + coins_gained,
        `total_coins_earned` = `total_coins_earned` + coins_gained;
    
    -- Check for level up (100 XP per level)
    SELECT `total_xp` INTO current_xp FROM `USER_GAME_STATS` WHERE `user_id` = NEW.user_id;
    SET new_level = FLOOR(current_xp / 100) + 1;
    
    UPDATE `USER_GAME_STATS` 
    SET `current_level` = new_level 
    WHERE `user_id` = NEW.user_id;
    
    -- Bonus XP for lucid dreams
    IF NEW.lucid = TRUE THEN
        INSERT INTO `XP_TRANSACTION` (`user_id`, `xp_amount`, `transaction_type`, `source_id`, `description`)
        VALUES (NEW.user_id, 50, 'LUCID_DREAM', NEW.dream_id, 'Lucid dream bonus');
        
        SET coins_gained = 5;
        INSERT INTO `COIN_TRANSACTION` (`user_id`, `coin_amount`, `transaction_type`, `source_id`, `description`)
        VALUES (NEW.user_id, coins_gained, 'EARNED', NEW.dream_id, 'Lucid dream bonus');
        
        UPDATE `USER_GAME_STATS` 
        SET `total_xp` = `total_xp` + 50,
            `dream_coins` = `dream_coins` + coins_gained,
            `total_coins_earned` = `total_coins_earned` + coins_gained
        WHERE `user_id` = NEW.user_id;
        
        -- Recalculate level
        SELECT `total_xp` INTO current_xp FROM `USER_GAME_STATS` WHERE `user_id` = NEW.user_id;
        SET new_level = FLOOR(current_xp / 100) + 1;
        UPDATE `USER_GAME_STATS` SET `current_level` = new_level WHERE `user_id` = NEW.user_id;
    END IF;
    
    -- Update streak
    CALL update_dream_streak(NEW.user_id, NEW.dream_date);
END//
DELIMITER ;

-- Stored Procedure: Update Dream Streak
DROP PROCEDURE IF EXISTS `update_dream_streak`;
DELIMITER //
CREATE PROCEDURE `update_dream_streak`(IN p_user_id INT, IN p_dream_date DATE)
BEGIN
    DECLARE v_current_streak INT DEFAULT 0;
    DECLARE v_longest_streak INT DEFAULT 0;
    DECLARE v_last_date DATE;
    DECLARE v_days_diff INT;
    
    -- Get current streak data
    SELECT `current_streak`, `longest_streak`, `last_dream_date`
    INTO v_current_streak, v_longest_streak, v_last_date
    FROM `DREAM_STREAK`
    WHERE `user_id` = p_user_id;
    
    -- Initialize if doesn't exist
    IF v_current_streak IS NULL THEN
        INSERT INTO `DREAM_STREAK` (`user_id`, `current_streak`, `longest_streak`, `last_dream_date`)
        VALUES (p_user_id, 1, 1, p_dream_date);
    ELSE
        -- Calculate days difference
        SET v_days_diff = DATEDIFF(p_dream_date, v_last_date);
        
        IF v_days_diff = 1 THEN
            -- Continue streak
            SET v_current_streak = v_current_streak + 1;
        ELSEIF v_days_diff = 0 THEN
            -- Same day, don't change
            SET v_current_streak = v_current_streak;
        ELSE
            -- Streak broken, reset
            SET v_current_streak = 1;
        END IF;
        
        -- Update longest streak
        IF v_current_streak > v_longest_streak THEN
            SET v_longest_streak = v_current_streak;
        END IF;
        
        -- Update table
        UPDATE `DREAM_STREAK`
        SET `current_streak` = v_current_streak,
            `longest_streak` = v_longest_streak,
            `last_dream_date` = p_dream_date
        WHERE `user_id` = p_user_id;
    END IF;
END//
DELIMITER ;

