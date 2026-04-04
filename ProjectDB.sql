-- USER table
CREATE TABLE IF NOT EXISTS `USER` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL,
    `email` VARCHAR(50) NOT NULL,
    `password` VARCHAR(50),
    `birthdate` DATE,
    `register_date` DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE `USER'
CHANGE COLUMN `name` `username` VARCHAR(50) NOT NULL;

-- DREAM table
CREATE TABLE IF NOT EXISTS `DREAM` (
    `dream_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `dname` VARCHAR(50) NOT NULL,
    `description` TEXT NOT NULL,
    `intensity` INT,
    `lucid` BOOLEAN,
    `dream_date` DATE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
);

ALTER TABLE `DREAM`
CHANGE COLUMN `name` `dname` VARCHAR(50) NOT NULL;

-- THEME, CATEGORY, EMOTION tables
CREATE TABLE IF NOT EXISTS `THEME` (
    `theme_id` INT AUTO_INCREMENT PRIMARY KEY,
    `theme_name` VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS `CATEGORY` (
    `category_id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_name` VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS `EMOTION` (
    `emotion_id` INT AUTO_INCREMENT PRIMARY KEY,
    `emotion_type` VARCHAR(100) NOT NULL
);

-- Junction tables
CREATE TABLE IF NOT EXISTS `DREAM_THEME` (
    `dream_id` INT NOT NULL,
    `theme_id` INT NOT NULL,
    PRIMARY KEY (`dream_id`, `theme_id`),
    FOREIGN KEY (`dream_id`) REFERENCES `DREAM`(`dream_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`theme_id`) REFERENCES `THEME`(`theme_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS `DREAM_CATEGORY` (
    `dream_id` INT NOT NULL,
    `category_id` INT NOT NULL,
    PRIMARY KEY (`dream_id`, `category_id`),
    FOREIGN KEY (`dream_id`) REFERENCES `DREAM`(`dream_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`category_id`) REFERENCES `CATEGORY`(`category_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS `DREAM_EMOTION` (
    `dream_id` INT NOT NULL,
    `emotion_id` INT NOT NULL,
    PRIMARY KEY (`dream_id`, `emotion_id`),
    FOREIGN KEY (`dream_id`) REFERENCES `DREAM`(`dream_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`emotion_id`) REFERENCES `EMOTION`(`emotion_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- DREAM_ANALYSIS table
CREATE TABLE IF NOT EXISTS `DREAM_ANALYSIS` (
    `analysis_id` INT AUTO_INCREMENT PRIMARY KEY,
    `dream_id` INT NOT NULL,
    `interpretation` TEXT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`dream_id`) REFERENCES `DREAM`(`dream_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- CHAT_SESSION table
CREATE TABLE IF NOT EXISTS `CHAT_SESSION` (
    `session_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `session_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `messages` TEXT,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- SUBSCRIPTION table
CREATE TABLE IF NOT EXISTS `SUBSCRIPTION` (
    `subscription_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE,
    `plan_type` ENUM('FREE_TRIAL', 'MONTHLY', 'YEARLY') NOT NULL,
    `status` ENUM('ACTIVE', 'EXPIRED', 'CANCELLED') DEFAULT 'ACTIVE',
    `auto_renew` BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (`user_id`) REFERENCES `USER`(`user_id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- PAYMENT table
CREATE TABLE IF NOT EXISTS `PAYMENT` (
    `payment_id` INT AUTO_INCREMENT PRIMARY KEY,
    `subscription_id` INT NOT NULL,
    `amount` DECIMAL(10,2) NOT NULL,
    `payment_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `payment_method` VARCHAR(50),
    `status` VARCHAR(20),
    FOREIGN KEY (`subscription_id`) REFERENCES `SUBSCRIPTION`(`subscription_id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


ALTER TABLE `USER` ADD UNIQUE (username);

ALTER TABLE USER MODIFY COLUMN password VARCHAR(255);

-- Added to prevent future duplicates:
ALTER TABLE EMOTION ADD UNIQUE (emotion_type);
ALTER TABLE THEME ADD UNIQUE (theme_name);
ALTER TABLE CATEGORY ADD UNIQUE (category_name);
ALTER TABLE USER ADD UNIQUE (email);  

-- Reset auto-increment
ALTER TABLE EMOTION AUTO_INCREMENT = 1;
ALTER TABLE THEME AUTO_INCREMENT = 1;
ALTER TABLE CATEGORY AUTO_INCREMENT = 1;

INSERT INTO EMOTION (emotion_type) VALUES
('Angry'),
('Anxious'),
('Calm'),
('Confused'),
('Content'),
('Curious'),
('Embarrassed'),
('Excited'),
('Fearful'),
('Frustrated'),
('Happy'),
('Hopeful'),
('Joyful'),
('Lonely'),
('Nostalgic'),
('Overwhelmed'),
('Peaceful'),
('Relieved'),
('Sad'),
('Surprised');

INSERT INTO THEME (theme_name) VALUES
('Animals'),
('Being Chased'),
('Childhood'),
('Death'),
('Falling'),
('Family'),
('Flying'),
('Friends'),
('Future'),
('Health'),
('Home'),
('Love/Romance'),
('Money'),
('Nakedness'),
('Nature'),
('Past'),
('School/Work'),
('Teeth'),
('Travel'),
('Water');

INSERT INTO CATEGORY (category_name) VALUES
('Abstract'),
('Adventure'),
('Fantasy'),
('Healing'),
('Lucid Dream'),
('Memory'),
('Nightmare'),
('Normal'),
('Prophetic'),
('Realistic'),
('Recurring'),
('Romantic'),
('Scary'),
('Symbolic'),
('Vivid');