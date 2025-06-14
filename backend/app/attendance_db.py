import os
import mysql.connector
from dotenv import load_dotenv
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger('attendance_db')


class AttendanceDB:
    """
    Database connector for MySQL to handle connections to attendance tables
    """

    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'gemba_digital'),
            'port': int(os.getenv('DB_PORT', '3306'))
        }
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor(dictionary=True)
            return True
        except mysql.connector.Error as err:
            logger.error(f"Database connection error: {err}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def validate_qr_token(self, qr_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate QR token against active gemba sessions

        Args:
            qr_token (str): The QR token to validate

        Returns:
            Optional[Dict[str, Any]]: Session data if valid, None otherwise
        """
        # QR token format: SESSION_YYYY_MM_DD_TXYZ
        # Extract session ID from the token
        try:
            if not qr_token.startswith("SESSION_"):
                logger.warning(f"Invalid QR token format: {qr_token}")
                return None

            parts = qr_token.split("_")
            if len(parts) < 5:
                logger.warning(f"Invalid QR token parts: {qr_token}")
                return None

            # Extract date from token
            try:
                year = int(parts[1])
                month = int(parts[2])
                day = int(parts[3])
                session_id_part = parts[4]

                # Check if session ID part starts with T
                if not session_id_part.startswith("T"):
                    logger.warning(
                        f"Invalid session ID format in token: {qr_token}")
                    return None

                # Extract numeric part of session ID
                session_id = int(session_id_part[1:])
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing QR token {qr_token}: {str(e)}")
                return None

            # Connect to database if not connected
            if not self.connection or not self.connection.is_connected():
                self.connect()

            # Query to check if session exists and is active
            query = """
            SELECT gs.id, gs.name, gs.status
            FROM genba_sessions gs
            WHERE gs.id = %s AND gs.status = 'PROGRESS'
            """

            self.cursor.execute(query, (session_id,))
            session = self.cursor.fetchone()

            if not session:
                logger.warning(
                    f"No active session found with ID: {session_id}")
                return None

            return session

        except Exception as e:
            logger.error(f"Error validating QR token: {str(e)}")
            return None

    def record_presence(self, user_id: str, session_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Record user presence for a session

        Args:
            user_id (str): User ID
            session_id (int): Session ID

        Returns:
            Tuple[bool, str, Dict[str, Any]]: Success status, message, and presence data
        """
        try:
            # Connect to database if not connected
            if not self.connection or not self.connection.is_connected():
                self.connect()

            # Check if user exists
            user_query = "SELECT id, name, role FROM users WHERE id = %s"
            self.cursor.execute(user_query, (user_id,))
            user = self.cursor.fetchone()

            if not user:
                return False, "User not found", {}

            # Check if user already has presence for this session
            check_query = """
            SELECT id, status, time_in, time_out 
            FROM attendances
            WHERE user_id = %s AND session_id = %s
            """
            self.cursor.execute(check_query, (user_id, session_id))
            existing_presence = self.cursor.fetchone()

            current_time = datetime.now()

            if existing_presence:
                # User already has presence record
                current_status = existing_presence['status']
                
                # log user as present or late based on start_time column from genba_session
                if current_status == "ABSENT": 
                    # Simulate current time (arrival/check-in time)
                    current_time = datetime.now()  # or however you're getting the arrival time

                    # Fetch full start_time from DB (not just the date)
                    session_query = "SELECT start_time FROM genba_sessions WHERE id = %s"
                    self.cursor.execute(session_query, (session_id,))
                    session_result = self.cursor.fetchone()

                    # Determine session start time
                    if not session_result:
                        # Fallback if session not found
                        session_start_time = current_time
                    else:
                        session_start_time = session_result['start_time']  # should be a datetime object

                    # Compare arrival time to session start time
                    status = 'LATE' if current_time > session_start_time else 'PRESENT'
                    
                    update_query = """
                    UPDATE attendances 
                    SET time_in = %s, updated_at = %s, status = %s
                    WHERE id = %s
                    """
                    self.cursor.execute(
                        update_query, (current_time, current_time, status,  existing_presence['id'], ))
                    self.connection.commit()

                    updated_data = {
                        "user_id": user_id,
                        "timestamp": current_time.isoformat(),
                        "status": status,
                        "time_in": current_time.isoformat(),
                        "time_out": None,
                        "user_name": user['name'],
                        "role": user['role']
                    }
                    
                    # Add pointss for attendance
                    self._add_attendance_pointss(user_id, status)

                    return True, "Presence updated successfully", updated_data
                
                # Log user out if user has clock in 
                elif existing_presence['time_out'] is None:
                    # First check-out: Update time_out while preserving the original status
                    update_query = """
                    UPDATE attendances 
                    SET time_out = %s, updated_at = %s
                    WHERE id = %s
                    """
                    self.cursor.execute(
                        update_query, (current_time, current_time, existing_presence['id']))
                    self.connection.commit()

                    # Return updated presence data with original status
                    updated_data = {
                        "user_id": user_id,
                        "timestamp": current_time.isoformat(),
                        "status": current_status,  # Maintain original status
                        "time_in": existing_presence['time_in'].isoformat() if existing_presence['time_in'] else None,
                        "time_out": current_time.isoformat(),
                        "user_name": user['name'],
                        "role": user['role']
                    }

                    return True, "Presence updated successfully", updated_data
                
                # Just return the data if user has clocked out 
                else:
                    # They've already signed out, just return the current data
                    existing_data = {
                        "user_id": user_id,
                        "timestamp": current_time.isoformat(),
                        "status": current_status,
                        "time_in": existing_presence['time_in'].isoformat() if existing_presence['time_in'] else None,
                        "time_out": existing_presence['time_out'].isoformat() if existing_presence['time_out'] else None,
                        "user_name": user['name'],
                        "role": user['role']
                    }

                    return True, "You have already signed out", existing_data
            
            # If user presence is none, create and record its status 
            else:
                # Determine if user is late based on session start time (9 AM)
                # Simulate current time (arrival/check-in time)
                current_time = datetime.now()  # or however you're getting the arrival time

                # Fetch full start_time from DB (not just the date)
                session_query = "SELECT start_time FROM genba_sessions WHERE id = %s"
                self.cursor.execute(session_query, (session_id,))
                session_result = self.cursor.fetchone()

                # Determine session start time
                if not session_result:
                    # Fallback if session not found
                    session_start_time = current_time
                else:
                    session_start_time = session_result['start_time']  # should be a datetime object

                # Compare arrival time to session start time
                status = 'LATE' if current_time > session_start_time else 'PRESENT'

                # Create new presence record
                insert_query = """
                INSERT INTO attendances 
                (user_id, session_id, status, time_in, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                self.cursor.execute(
                    insert_query, (user_id, session_id, status, current_time, current_time, current_time))
                self.connection.commit()

                # Get inserted record ID
                presence_id = self.cursor.lastrowid

                # Add pointss for attendance
                self._add_attendance_pointss(user_id, status)

                # Return new presence data
                new_data = {
                    "user_id": user_id,
                    "timestamp": current_time.isoformat(),
                    "status": status,
                    "time_in": current_time.isoformat(),
                    "time_out": None,
                    "user_name": user['name'],
                    "role": user['role']
                }

                message = "Presence recorded successfully" if status == "present" else "Late attendance recorded"
                return True, message, new_data

        except Exception as e:
            logger.error(f"Error recording presence: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False, f"Error recording presence: {str(e)}", {}

    def _add_attendance_pointss(self, user_id: str, status: str = 'PRESENT') -> bool:
        """
        Add pointss to user for attendance

        Args:
            user_id (str): User ID
            status (str): Attendance status ('present' or 'late')

        Returns:
            bool: Success status
        """
        try:
            # Connect to database if not connected
            if not self.connection or not self.connection.is_connected():
                self.connect()

            # Get current user pointss
            user_query = "SELECT points FROM users WHERE id = %s"
            self.cursor.execute(user_query, (user_id,))
            user = self.cursor.fetchone()

            if not user:
                logger.warning(f"User not found for adding pointss: {user_id}")
                return False

            current_pointss = user['points'] or 0
            # pointss based on attendance status
            # 10 pointss for present, 5 for late
            pointss_to_add = 10 if status == 'PRESENT' else 5
            new_pointss = current_pointss + pointss_to_add

            # Update user pointss
            update_query = "UPDATE users SET points = %s WHERE id = %s"
            self.cursor.execute(update_query, (new_pointss, user_id))

            # Record points history
            current_time = datetime.now()
            history_query = """
            INSERT INTO point_histories 
            (userid, type, category, point_before, point_earned, point_after, created_at, updated_at)
            VALUES (%s, 'INC', 'PRE', %s, %s, %s, %s, %s)
            """
            self.cursor.execute(history_query, (
                user_id,
                current_pointss,
                pointss_to_add,
                new_pointss,
                current_time,
                current_time
            ))

            self.connection.commit()
            return True

        except Exception as e:
            logger.error(f"Error adding attendance pointss: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def add_root_cause_pointss(self, user_id: str, score: float) -> bool:
        """
        Add pointss to user for root cause scoring

        Args:
            user_id (str): User ID
            score (float): Score from root cause evaluation (0-10)

        Returns:
            bool: Success status
        """
        print(f"Adding root cause pointss - User ID: {user_id}, Score: {score}")
        try:
            # Connect to database if not connected
            if not self.connection or not self.connection.is_connected():
                self.connect()

            # Get current user pointss
            user_query = "SELECT points FROM users WHERE id = %s"
            self.cursor.execute(user_query, (user_id,))
            user = self.cursor.fetchone()

            if not user:
                logger.warning(f"User not found for adding pointss: {user_id}")
                return False

            current_pointss = user['points'] or 0

            # Use the score directly (already in 1-100 range from AI)
            pointss_to_add = max(1, min(100, int(score)))
            new_pointss = current_pointss + pointss_to_add

            # Update user pointss
            update_query = "UPDATE users SET points = %s WHERE id = %s"
            self.cursor.execute(update_query, (new_pointss, user_id))

            # Record points history
            current_time = datetime.now()
            # Debug log before executing query
            print(f"Executing points history query with category: 'rootcause_scoring'")

            history_query = """
            INSERT INTO points_history 
            (user_id, type, category, points_before, points, points_after, created_at, updated_at)
            VALUES (%s, 'add', 'rootcause_scoring', %s, %s, %s, %s, %s)
            """
            self.cursor.execute(history_query, (
                user_id,
                current_pointss,
                pointss_to_add,
                new_pointss,
                current_time,
                current_time
            ))

            self.connection.commit()
            return True

        except Exception as e:
            logger.error(f"Error adding root cause pointss: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def get_session_attendees(self, session_id: int) -> list:
        """
        Get list of attendees for a session

        Args:
            session_id (int): Session ID

        Returns:
            list: List of attendees with presence data
        """
        try:
            # Connect to database if not connected
            if not self.connection or not self.connection.is_connected():
                self.connect()

            query = """
            SELECT p.id, p.user_id, p.status, p.time_in, p.time_out,
                   u.name, u.role, u.email
            FROM attendances p
            JOIN users u ON p.user_id = u.id
            WHERE p.session_id = %s
            ORDER BY p.time_in DESC
            """

            self.cursor.execute(query, (session_id,))
            attendees = self.cursor.fetchall()

            # Format datetime objects for JSON serialization
            formatted_attendees = []
            for attendee in attendees:
                formatted_attendee = dict(attendee)
                formatted_attendee['time_in'] = attendee['time_in'].isoformat(
                ) if attendee['time_in'] else None
                formatted_attendee['time_out'] = attendee['time_out'].isoformat(
                ) if attendee['time_out'] else None
                formatted_attendees.append(formatted_attendee)

            return formatted_attendees

        except Exception as e:
            logger.error(f"Error getting session attendees: {str(e)}")
            return []
