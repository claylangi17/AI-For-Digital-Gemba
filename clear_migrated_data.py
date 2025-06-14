import mysql.connector
import logging

# --- Database Configuration (same as migrate_gemba_data.py) ---
DB_CONFIG = {
    'host': 'aradenta.com',
    'user': 'aradenta_genba_external',
    'password': 'yournameonit',
    'database': 'aradenta_genba_digital'
}

# --- Logger Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_data():
    """Connects to the database and clears data from specified tables."""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info(f"Successfully connected to the database '{DB_CONFIG['database']}'.")

        tables_to_clear = ['actions', 'root_causes', 'issues', 'lines']

        cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
        logger.info("Disabled foreign key checks.")

        for table_name in tables_to_clear:
            try:
                logger.info(f"Attempting to TRUNCATE table `{table_name}`...")
                cursor.execute(f"TRUNCATE TABLE `{table_name}`;")
                logger.info(f"Successfully TRUNCATED table `{table_name}`.")
            except mysql.connector.Error as err:
                logger.error(f"Error truncating table `{table_name}`: {err}")
                # Optionally, re-raise or handle more gracefully

        cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
        logger.info("Re-enabled foreign key checks.")

        conn.commit()
        logger.info("All specified tables have been cleared and changes committed.")

    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        if conn and conn.is_connected():
            conn.rollback()
            logger.info("Transaction rolled back due to error.")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    logger.info("Starting script to clear migrated Gemba data...")
    # IMPORTANT: Remind user to confirm before running if this were interactive
    # For agent execution, we proceed based on user's explicit request.
    clear_data()
    logger.info("Data clearing script finished.")
