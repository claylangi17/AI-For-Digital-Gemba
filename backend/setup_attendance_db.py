import os
import mysql.connector
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'digital_gemba'),
    'port': int(os.getenv('DB_PORT', '3306'))
}

def setup_database():
    """
    Setup attendance database tables if they don't exist
    """
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # Create users table if not exists
        logger.info("Setting up users table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            point INT DEFAULT 0,
            image_path TEXT,
            email VARCHAR(255) UNIQUE,
            email_verified_at TIMESTAMP NULL,
            role ENUM('admin', 'user') DEFAULT 'user',
            password VARCHAR(255) NOT NULL,
            remember_token VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        
        # Note: Face recognition table not created as it's not used
        
        # Create presences table if not exists
        logger.info("Setting up presences table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS presences (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            userid BIGINT NOT NULL,
            session_id BIGINT NOT NULL,
            status ENUM('present', 'absent', 'late') DEFAULT 'present',
            time_in TIMESTAMP NULL,
            time_out TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (userid) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
        
        # Create point_history table if not exists
        logger.info("Setting up point_history table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS point_history (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            userid BIGINT NOT NULL,
            type ENUM('add', 'subtract') NOT NULL,
            category ENUM('attendance', 'participation', 'contribution', 'achievement', 'other') NOT NULL,
            point_before INT NOT NULL,
            point INT NOT NULL,
            point_after INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (userid) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
        
        # Create gemba_sessions table if not exists
        logger.info("Setting up gemba_sessions table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gemba_sessions (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            area VARCHAR(255),
            problem_description TEXT,
            supporting_files TEXT,
            whiteboard_id BIGINT,
            root_cause_ids TEXT,
            solutions_ids TEXT,
            choosen_solution_id BIGINT,
            status ENUM('draft', 'active', 'completed', 'archived') DEFAULT 'draft',
            time_spent INT,
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        
        # Create gemba_areas table if not exists
        logger.info("Setting up gemba_areas table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gemba_areas (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        
        # Insert test data if tables are empty
        logger.info("Checking if test data is needed...")
        
        # Check if users table is empty
        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info("Inserting test users...")
            # Insert test users (with hashed passwords)
            cursor.execute("""
            INSERT INTO users (name, email, password, role) VALUES
            ('John Smith', 'john@example.com', '$2b$12$1234567890123456789012uQi10bKRgRzl9XuJQxhzLp1nFQ5YHYe', 'admin'),
            ('Sarah Johnson', 'sarah@example.com', '$2b$12$1234567890123456789012uQi10bKRgRzl9XuJQxhzLp1nFQ5YHYe', 'user'),
            ('Mike Williams', 'mike@example.com', '$2b$12$1234567890123456789012uQi10bKRgRzl9XuJQxhzLp1nFQ5YHYe', 'user')
            """)
        
        # Check if gemba_areas table is empty
        cursor.execute("SELECT COUNT(*) as count FROM gemba_areas")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info("Inserting test areas...")
            # Insert test areas
            cursor.execute("""
            INSERT INTO gemba_areas (name, description) VALUES
            ('Production Line A', 'Main assembly line for product A'),
            ('Production Line B', 'Secondary assembly line for product B'),
            ('Warehouse', 'Main storage area for finished goods')
            """)
            
        # Check if gemba_sessions table is empty
        cursor.execute("SELECT COUNT(*) as count FROM gemba_sessions")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info("Inserting test sessions...")
            # Insert test sessions
            cursor.execute("""
            INSERT INTO gemba_sessions (name, area, status, created_by) VALUES
            ('Morning Inspection', 'Production Line A', 'active', 1),
            ('Afternoon Inspection', 'Production Line B', 'active', 1),
            ('Inventory Check', 'Warehouse', 'draft', 1)
            """)
            
        connection.commit()
        logger.info("Database setup completed successfully!")
        
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            logger.info("MySQL connection closed")

if __name__ == "__main__":
    setup_database()
