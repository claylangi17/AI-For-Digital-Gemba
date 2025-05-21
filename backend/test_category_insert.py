import os
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Database connection details from environment variables
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'digital_gemba'),
    'port': int(os.getenv('DB_PORT', '3306'))
}

try:
    # Connect to the database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    
    # Test insert with various category formats
    user_id = 2
    current_points = 50
    points_to_add = 25
    new_points = current_points + points_to_add
    current_time = datetime.now()
    
    # Format 1: Using concatenated SQL string with quotes
    query1 = """
    INSERT INTO point_history 
    (userid, type, category, point_before, point, point_after, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(query1, (
        user_id,
        'add',
        'test_category_1',  # Test category name
        current_points,
        points_to_add,
        new_points,
        current_time,
        current_time
    ))
    
    print("Insert 1 completed with category 'test_category_1'")
    
    # Format 2: Using MySQL-specific syntax
    query2 = """
    INSERT INTO point_history 
    (userid, type, category, point_before, point, point_after, created_at, updated_at)
    VALUES (%s, 'add', 'test_category_2', %s, %s, %s, %s, %s)
    """
    
    cursor.execute(query2, (
        user_id,
        current_points + 100,
        points_to_add,
        new_points + 100,
        current_time,
        current_time
    ))
    
    print("Insert 2 completed with hardcoded category 'test_category_2'")
    
    # Commit changes
    connection.commit()
    print("All changes committed")
    
    # Check what was actually inserted
    cursor.execute("SELECT * FROM point_history WHERE category IN ('test_category_1', 'test_category_2')")
    results = cursor.fetchall()
    
    print(f"Results from database ({len(results)} records):")
    for row in results:
        print(f"ID: {row['id']}, UserID: {row['userid']}, Category: '{row['category']}', Points: {row['point']}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    if 'connection' in locals() and connection.is_connected():
        connection.rollback()
finally:
    if 'cursor' in locals() and cursor:
        cursor.close()
    if 'connection' in locals() and connection.is_connected():
        connection.close()
        print("Database connection closed")
