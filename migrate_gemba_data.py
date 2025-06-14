import mysql.connector
import re
from datetime import datetime
import logging

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Database Configuration ---
# !!! USER: PLEASE FILL IN YOUR DATABASE DETAILS HERE !!!
DB_CONFIG = {
    'host': 'aradenta.com',         # e.g., 'localhost' or IP address
    'user': 'aradenta_genba_external',    # Your MySQL username
    'password': 'yournameonit', # Your MySQL password
    'database': 'aradenta_genba_digital' # Your database name
}

# --- SQL Dump File Path ---
# Update this path if your gemba_issues.sql file is located elsewhere
SQL_DUMP_FILE_PATH = r'd:\Coding\AI For Digital Gemba\gemba_issues.sql'

# --- Default Values (as provided by user) ---
DEFAULT_USER_ID = 1
DEFAULT_SESSION_ID = 5
DEFAULT_ISSUE_ITEMS = "Migrated Data"
DEFAULT_ISSUE_ASSIGNED_IDS = "N/A"  # If this field expects JSON, "[]" might be more appropriate
DEFAULT_ISSUE_STATUS = "CLOSED"
# lines.description will use the 'area' value from the old data
DEFAULT_ACTION_STATUS = "FINISHED"


def parse_value(value_str):
    """Converts a string value from SQL dump to a Python type."""
    value_str = value_str.strip()
    if value_str == 'NULL':
        return None
    if value_str.startswith("'") and value_str.endswith("'"):
        # Process content within quotes
        inner_content = value_str[1:-1]
        # SQL escapes ' as ''. Replace '' with ' first.
        # Then handle standard backslash escapes.
        return inner_content.replace("''", "'") \
                            .replace("\\'", "'") \
                            .replace('\\"', '"') \
                            .replace('\\n', '\n') \
                            .replace('\\r', '\r') \
                            .replace('\\t', '\t') \
                            .replace('_x000B_', '\n') # Treat Excel's vertical tab as newline
    try:
        return int(value_str)
    except ValueError:
        pass
    try:
        return float(value_str)
    except ValueError:
        pass 
    return value_str # Should be a date string or other unquoted literal

def parse_csv_line_robustly(line_text, delimiter=',', quote_char="'"):
    """
    Parses a CSV-like string (content of one SQL data tuple) into a list of raw field strings.
    Handles quoted fields containing delimiters or newlines, and SQL's '' escape for a single quote.
    """
    fields = []
    current_field = []
    in_quotes = False
    idx = 0
    n = len(line_text)

    while idx < n:
        char = line_text[idx]

        if not in_quotes:
            if char == quote_char:
                in_quotes = True
                current_field.append(char) # Keep the quote for parse_value to strip
            elif char == delimiter:
                fields.append("".join(current_field))
                current_field = []
            else:
                current_field.append(char)
        else: # in_quotes is True
            if char == '\\': # Escape character
                if idx + 1 < n: # Check if there's a next character to escape
                    current_field.append(char) # Keep the backslash
                    current_field.append(line_text[idx+1]) # Keep the escaped character
                    idx += 1 # Advance index past the escaped character
                else: # Backslash at the very end of the string, just keep it
                    current_field.append(char)
            elif char == quote_char:
                # Check for SQL's double quote escape ('') vs. a closing quote
                if idx + 1 < n and line_text[idx+1] == quote_char:
                    current_field.append(quote_char) # Add one actual quote for ''
                    idx += 1 # Skip the second quote of the pair
                else: # This is a closing quote
                    in_quotes = False
                    current_field.append(char) # Keep the closing quote
            else:
                current_field.append(char) # Accumulate content within quotes
        idx += 1
    
    fields.append("".join(current_field)) # Add the last field
    return fields

def parse_data_tuples_from_string(data_block_string):
    """
    Extracts tuples of values from a string containing a block of data tuples from an INSERT statement.
    This version manually parses to find top-level tuples, respecting quotes and parenthesis nesting.
    """
    parsed_rows = []
    paren_level = 0
    in_quotes = False
    quote_char_used = ''
    current_tuple_start_index = -1
    idx = 0
    n = len(data_block_string)

    while idx < n:
        char = data_block_string[idx]

        if in_quotes:
            if char == '\\': # Backslash escape
                if idx + 1 < n: # Ensure there's a char to skip
                    idx += 1 # Effectively skip the escaped character for quote logic
            elif char == quote_char_used:
                in_quotes = False
                quote_char_used = ''
        else: # Not in quotes
            if char == "'": # Assuming single quotes for SQL string literals
                in_quotes = True
                quote_char_used = "'"
            elif char == '(':
                if paren_level == 0: # Start of a new top-level tuple's content
                    current_tuple_start_index = idx + 1
                paren_level += 1
            elif char == ')':
                paren_level -= 1
                if paren_level == 0 and current_tuple_start_index != -1:
                    # End of a top-level tuple
                    content_inside_paren = data_block_string[current_tuple_start_index:idx]
                    try:
                        raw_fields = parse_csv_line_robustly(content_inside_paren)
                        values = [parse_value(rf.strip()) for rf in raw_fields]
                        
                        if len(values) == 9:
                            parsed_rows.append(tuple(values))
                        else:
                            logger.warning(f"Skipping row with unexpected number of values ({len(values)} instead of 9) in tuple '{content_inside_paren[:150].replace(chr(10), ' ')}...': first few values {str(values[:3])[:100]}...")
                    except Exception as e:
                        logger.error(f"Error processing tuple content '{content_inside_paren[:150].replace(chr(10), ' ')}...': {e}", exc_info=True)
                    current_tuple_start_index = -1 # Reset for the next tuple
        idx += 1
        
    return parsed_rows

def get_or_create_line(cursor, area_name, created_at_dt):
    """Gets existing line_id or creates a new line, handling potentially out-of-range dates."""
    safe_insert_date = created_at_dt
    default_date_str = "2025-06-03 21:21:31"
    default_datetime_obj = datetime.strptime(default_date_str, '%Y-%m-%d %H:%M:%S')

    # Heuristic: MySQL TIMESTAMP valid range starts from 1970. DATETIME from 1000.
    # Given errors for '1901', checking for year < 1970 is a safeguard.
    if created_at_dt.year < 1970:
        logger.warning(f"Date {created_at_dt.strftime('%Y-%m-%d')} for line '{area_name}' is potentially out of DB range. Using default: {default_date_str}")
        safe_insert_date = default_datetime_obj

    select_query = "SELECT `id` FROM `lines` WHERE `name` = %s"
    cursor.execute(select_query, (area_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        insert_query = """
        INSERT INTO `lines` (`name`, `description`, `created_at`, `updated_at`)
        VALUES (%s, %s, %s, %s)
        """
        try:
            cursor.execute(insert_query, (area_name, area_name, safe_insert_date, safe_insert_date))
            return cursor.lastrowid
        except mysql.connector.Error as err:
            logger.error(f"DB error in get_or_create_line for area '{area_name}' with date {safe_insert_date}: {err}")
            # If insertion fails even with default, try with an absolute failsafe date or re-raise
            if safe_insert_date != default_datetime_obj: # If it wasn't already the default
                logger.info(f"Retrying get_or_create_line for '{area_name}' with hardcoded default date due to error.")
                cursor.execute(insert_query, (area_name, area_name, default_datetime_obj, default_datetime_obj))
                return cursor.lastrowid
            raise # Re-raise if already tried default or for other errors

def main():
    logger.info("Starting Gemba data migration script.")
    
    raw_data_rows = []
    parsing_insert_block = False
    current_insert_buffer = []
    try:
        with open(SQL_DUMP_FILE_PATH, 'r', encoding='utf-8') as f:
            logger.info(f"Opened SQL dump file: {SQL_DUMP_FILE_PATH}")
            for line_number, line_content in enumerate(f, 1):
                stripped_line = line_content.strip()

                if not stripped_line: # Skip empty lines
                    continue

                if stripped_line.upper().startswith('INSERT INTO `GEMBA_ISSUES`'):
                    if parsing_insert_block:
                        # This case should ideally not happen if SQL is well-formed (no nested INSERTs for same table without ';')
                        logger.warning(f"Line {line_number}: New INSERT statement started while already parsing one. Processing previous block.")
                        if current_insert_buffer:
                            full_block_string = " ".join(current_insert_buffer)
                            # Extract only the values part: from first '(' to last ')' before potential ';'
                            try:
                                values_part = full_block_string[full_block_string.index('(') : full_block_string.rindex(')')+1]
                                parsed_block_rows = parse_data_tuples_from_string(values_part)
                                if parsed_block_rows:
                                    raw_data_rows.extend(parsed_block_rows)
                                    logger.debug(f"Processed {len(parsed_block_rows)} rows from previous buffered INSERT block.")
                            except ValueError: # If '(' or ')' not found
                                logger.error(f"Could not find start/end of data tuples in buffered block: {full_block_string[:200]}...")
                        current_insert_buffer = [] # Reset for the new INSERT
                    
                    parsing_insert_block = True
                    logger.info(f"Line {line_number}: Detected INSERT INTO gemba_issues. Starting to buffer data.")
                    # Add the line, specifically the part after VALUES if VALUES is on this line
                    values_keyword_pos = stripped_line.upper().find('VALUES')
                    if values_keyword_pos != -1:
                        line_to_add = stripped_line[values_keyword_pos + len('VALUES'):].strip()
                        if line_to_add: # Ensure there's content after VALUES to add
                           current_insert_buffer.append(line_to_add)
                    # If VALUES is not on this line, the first line of data (starting with '(') will be caught next
                    continue

                if parsing_insert_block:
                    current_insert_buffer.append(stripped_line) # Add the current line to buffer
                    if stripped_line.endswith(';'):
                        logger.info(f"Line {line_number}: Detected end of INSERT statement (';'). Processing buffered block.")
                        full_block_string = " ".join(current_insert_buffer)
                        current_insert_buffer = [] # Reset buffer
                        parsing_insert_block = False
                        
                        # Extract only the values part: from first '(' to last ')' before potential ';'
                        try:
                            # Ensure we only take content between the first '(' and the last ')'
                            # This handles cases where 'VALUES' might be followed by comments or other SQL before tuples start
                            first_paren_index = full_block_string.index('(')
                            # Find the last ')' that is followed by a ';' or is at the end of the string (after stripping trailing ';')
                            temp_str_for_rindex = full_block_string.rstrip()
                            if temp_str_for_rindex.endswith(';'):
                                temp_str_for_rindex = temp_str_for_rindex[:-1].rstrip()
                            last_paren_index = temp_str_for_rindex.rindex(')')
                            
                            values_part = full_block_string[first_paren_index : last_paren_index+1]
                            parsed_block_rows = parse_data_tuples_from_string(values_part)
                            if parsed_block_rows:
                                raw_data_rows.extend(parsed_block_rows)
                                logger.info(f"Successfully parsed {len(parsed_block_rows)} data tuples from buffered INSERT block ending at line {line_number}.")
                            else:
                                logger.warning(f"No data tuples parsed from buffered INSERT block ending at line {line_number}. Content snippet: {values_part[:200]}...")
                        except ValueError: # If '(' or ')' not found, or other string processing errors
                            logger.error(f"Could not find start/end of data tuples in buffered block from INSERT ending line {line_number}: {full_block_string[:200]}...")
        
        if parsing_insert_block and current_insert_buffer: # If loop ended mid-block (e.g. EOF)
            logger.warning("SQL dump parsing finished while still in an active insert block (missing terminal ';'? EOF reached?). Processing remaining buffer.")
            full_block_string = " ".join(current_insert_buffer)
            try:
                first_paren_index = full_block_string.index('(')
                temp_str_for_rindex = full_block_string.rstrip()
                if temp_str_for_rindex.endswith(';'):
                    temp_str_for_rindex = temp_str_for_rindex[:-1].rstrip()
                last_paren_index = temp_str_for_rindex.rindex(')')
                values_part = full_block_string[first_paren_index : last_paren_index+1]
                parsed_block_rows = parse_data_tuples_from_string(values_part)
                if parsed_block_rows:
                    raw_data_rows.extend(parsed_block_rows)
                    logger.debug(f"Processed {len(parsed_block_rows)} rows from final buffered INSERT block.")
            except ValueError:
                logger.error(f"Could not find start/end of data tuples in final buffered block: {full_block_string[:200]}...")

        if not raw_data_rows:
            logger.info("No data rows were extracted after full parsing. Check SQL dump for 'INSERT INTO `GEMBA_ISSUES`' statements and their data format.")
        else:
            logger.info(f"Successfully parsed a total of {len(raw_data_rows)} raw data rows from {SQL_DUMP_FILE_PATH} after full parsing.")
    except FileNotFoundError:
        logger.error(f"SQL dump file not found: {SQL_DUMP_FILE_PATH}")
        return
    except Exception as e:
        logger.error(f"Error parsing SQL dump file: {e}")
        return

    if not raw_data_rows:
        logger.info("No data rows found in the SQL dump file. Exiting.")
        return

    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info("Successfully connected to the database.")

        for i, row_data in enumerate(raw_data_rows):
            try:
                (
                    old_id, raw_date, area, problem, root_cause_desc, 
                    temp_action, prev_action, source_file, category
                ) = row_data

                # Convert date string to datetime object, using default for invalid/out-of-range dates
                default_date_str = "2025-06-03 21:21:31"
                default_datetime_obj = datetime.strptime(default_date_str, '%Y-%m-%d %H:%M:%S')
                created_at_datetime = default_datetime_obj # Initialize with default

                if raw_date and raw_date.strip():
                    try:
                        parsed_dt = datetime.strptime(raw_date, '%Y-%m-%d')
                        # Heuristic: Check if parsed date's year is before 1970 (common for TIMESTAMP issues)
                        if parsed_dt.year < 1970:
                            logger.warning(f"Raw date {raw_date} (Old ID: {old_id}) has year {parsed_dt.year} < 1970. Using default: {default_date_str}")
                            created_at_datetime = default_datetime_obj
                        else:
                            created_at_datetime = parsed_dt
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid date format '{raw_date}' (Old ID: {old_id}). Error: {e}. Using default: {default_date_str}")
                        created_at_datetime = default_datetime_obj
                else:
                    logger.warning(f"Empty or invalid raw_date (Old ID: {old_id}). Using default: {default_date_str}")
                    created_at_datetime = default_datetime_obj
                
                # Now, created_at_datetime holds either the validly parsed date or the default_datetime_obj
                
                # 1. Get or Create Line
                line_id = get_or_create_line(cursor, area, created_at_datetime)

                # 2. Insert Issue
                # legacy_id column will not be used as per user request.
                issue_insert_query = """
                INSERT INTO issues (session_id, line_id, items, assigned_ids, description, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                issue_values = (
                    DEFAULT_SESSION_ID, line_id, DEFAULT_ISSUE_ITEMS,
                    DEFAULT_ISSUE_ASSIGNED_IDS, problem, DEFAULT_ISSUE_STATUS,
                    created_at_datetime, created_at_datetime
                )
                cursor.execute(issue_insert_query, issue_values)
                issue_id = cursor.lastrowid

                # 3. Insert Root Cause
                if root_cause_desc:
                    rc_insert_query = """
                    INSERT INTO root_causes (issue_id, category, description, created_by, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    rc_values = (
                        issue_id, category, root_cause_desc, DEFAULT_USER_ID, 
                        created_at_datetime, created_at_datetime
                    )
                    cursor.execute(rc_insert_query, rc_values)
                    root_cause_id = cursor.lastrowid
                else:
                    root_cause_id = None # No root cause described
                    logger.info(f"No root cause description for old issue ID {old_id}, skipping root cause insertion.")

                # 4. Insert Actions (if root_cause_id is available)
                if root_cause_id:
                    action_insert_query = """
                    INSERT INTO actions (issue_id, root_cause_id, type, description, pic_id, due_date, status, created_by, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    # Temporary Action (Corrective)
                    if temp_action:
                        # due_date can be set to created_at_datetime or NULL if not applicable
                        action_values_corrective = (
                            issue_id, root_cause_id, 'CORRECTIVE', temp_action, 
                            DEFAULT_USER_ID, created_at_datetime, DEFAULT_ACTION_STATUS, 
                            DEFAULT_USER_ID, created_at_datetime, created_at_datetime
                        )
                        cursor.execute(action_insert_query, action_values_corrective)
                    
                    # Preventive Action
                    if prev_action:
                        action_values_preventive = (
                            issue_id, root_cause_id, 'PREVENTIVE', prev_action, 
                            DEFAULT_USER_ID, created_at_datetime, DEFAULT_ACTION_STATUS, 
                            DEFAULT_USER_ID, created_at_datetime, created_at_datetime
                        )
                        cursor.execute(action_insert_query, action_values_preventive)
                elif temp_action or prev_action:
                     logger.warning(f"Actions found for old issue ID {old_id} but no root cause was inserted. Actions will not be linked to a root cause.")
                     # Decide if actions should be inserted without root_cause_id (would require schema change or different logic)

                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1} records...")
                    conn.commit() # Commit periodically

            except mysql.connector.Error as err:
                logger.error(f"Database error processing row {i+1} (Old ID: {row_data[0] if row_data else 'N/A'}): {err}")
                # conn.rollback() # Optional: rollback this specific row's transaction if needed, or handle at end
            except Exception as e:
                logger.error(f"Generic error processing row {i+1} (Old ID: {row_data[0] if row_data else 'N/A'}): {e}")

        conn.commit() # Final commit
        logger.info("Data migration completed successfully!")

    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        if conn: 
            conn.rollback()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        if conn: 
            conn.rollback()
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    main()

