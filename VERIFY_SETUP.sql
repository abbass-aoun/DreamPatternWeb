-- ========================================
-- VERIFICATION QUERIES
-- Run these in HeidiSQL to verify setup
-- ========================================

-- 1. Check if all game tables were created
SHOW TABLES LIKE '%GAME%';
SHOW TABLES LIKE '%ACHIEVEMENT%';
SHOW TABLES LIKE '%STREAK%';
SHOW TABLES LIKE '%SHOP%';
SHOW TABLES LIKE '%REALITY%';

-- 2. Check if trigger exists
SHOW TRIGGERS LIKE 'award_xp_on_dream';

-- 3. Check if stored procedure exists
SHOW PROCEDURE STATUS WHERE Name = 'update_dream_streak';

-- 4. Check if achievements were inserted (should see 8 achievements)
SELECT * FROM ACHIEVEMENT;

-- 5. Check if shop items were inserted (should see 6 items)
SELECT * FROM DREAM_SHOP;

-- 6. Check if any user has game stats (will be empty if no dreams recorded yet)
SELECT * FROM USER_GAME_STATS;

-- 7. Check foreign key constraints are working
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
AND REFERENCED_TABLE_NAME = 'USER'
AND TABLE_NAME LIKE '%GAME%' OR TABLE_NAME LIKE '%ACHIEVEMENT%' OR TABLE_NAME LIKE '%STREAK%' OR TABLE_NAME LIKE '%SHOP%' OR TABLE_NAME LIKE '%REALITY%';





















