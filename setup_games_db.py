#!/usr/bin/env python3
"""
Setup Games Database Tables
Run this script to create the games and leaderboard tables
"""

import mysql.connector
from mysql.connector import Error
import os

def setup_games_database():
    """Setup the games and leaderboard database tables"""
    
    # Database connection parameters
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'aabbcc123',  # Database password from db.py
        'database': 'dream_pattern_db',
        'port': 3307  # Database port from db.py
    }
    
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(**db_config)
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            print("✅ Connected to MySQL database")
            
            # Read and execute the games database SQL
            sql_file_path = os.path.join(os.path.dirname(__file__), 'GAMES_LEADERBOARD_DATABASE.sql')
            
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                sql_script = file.read()
            
            # Split the script into individual statements
            sql_statements = sql_script.split(';')
            
            for statement in sql_statements:
                if statement.strip():
                    try:
                        cursor.execute(statement)
                        print(f"✅ Executed: {statement[:50]}...")
                    except Error as e:
                        if "already exists" not in str(e) and "duplicate" not in str(e).lower():
                            print(f"⚠️  Warning: {e}")
            
            connection.commit()
            print("✅ Games database setup completed successfully!")
            
            # Verify tables were created
            cursor.execute("SHOW TABLES LIKE 'GAME'")
            game_table = cursor.fetchone()
            
            cursor.execute("SHOW TABLES LIKE 'GAME_SCORE'")
            score_table = cursor.fetchone()
            
            if game_table and score_table:
                print("✅ GAME and GAME_SCORE tables verified!")
                
                # Show the games that were inserted
                cursor.execute("SELECT * FROM GAME")
                games = cursor.fetchall()
                
                print("\n🎮 Available Games:")
                for game in games:
                    print(f"   - {game[1]} {game[3]}: {game[2]}")
            else:
                print("❌ Tables were not created properly")
            
    except Error as e:
        print(f"❌ Database error: {e}")
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("✅ Database connection closed")

if __name__ == "__main__":
    setup_games_database()
