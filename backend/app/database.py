import os
import mysql.connector
from dotenv import load_dotenv
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger('database')

class DatabaseConnector:
    """
    Database connector for MySQL to handle connections to the gemba_issues table
    with semantic search capabilities for improved data retrieval
    """
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'digital_gemba'),
            'port': int(os.getenv('DB_PORT', '3306'))
        }
        self.connection = None
        self.cursor = None
        
        # Initialize the sentence transformer model for semantic search
        # Using a multilingual model that works well with Indonesian and English text
        try:
            self.sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("Sentence transformer model loaded successfully in database connector")
        except Exception as e:
            logger.error(f"Error loading sentence transformer model in database connector: {str(e)}")
            self.sentence_model = None

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor(dictionary=True)
            return True
        except mysql.connector.Error as err:
            print(f"Database connection error: {err}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


    def get_optimized_data_by_area_and_category(self, area, category):
        """
        Fetch only essential columns (area, problem, root_cause, category) filtered by area and category
        to optimize token usage for AI processing
        
        Args:
            area (str): The area to filter data by
            category (str): The category to filter data by
        Returns:
            list: A list of dictionaries containing only essential columns
        """
        query = """
        SELECT area, problem, root_cause, category FROM gemba_issues 
        WHERE area LIKE %s AND category LIKE %s
        ORDER BY date DESC
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            self.cursor.execute(query, (f"%{area}%", f"%{category}%"))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error fetching optimized data: {err}")
            return []
            
    def get_action_data_by_area_and_category(self, area, category):
        """
        Fetch data including action fields (temporary_action, preventive_action) filtered by area and category
        for action suggestion processing
        
        Args:
            area (str): The area to filter data by
            category (str): The category to filter data by
        Returns:
            list: A list of dictionaries containing all necessary fields for action suggestions
        """
        query = """
        SELECT area, problem, root_cause, category, temporary_action, preventive_action 
        FROM gemba_issues 
        WHERE area LIKE %s AND category LIKE %s
        ORDER BY date DESC
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            self.cursor.execute(query, (f"%{area}%", f"%{category}%"))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            logger.error(f"Error fetching action data: {err}")
            return []
            
    def _filter_by_semantic_similarity(self, query_text: str, data: List[Dict[str, Any]], 
                                     field_to_match: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Generic helper method to filter data based on semantic similarity
        
        Args:
            query_text (str): The text to compare against
            data (list): List of data dictionaries to filter
            field_to_match (str): The field in the dictionaries to compare against
            top_k (int): Number of most relevant records to return
            
        Returns:
            list: List of most semantically relevant records
        """
        if not self.sentence_model or not data:
            logger.warning("Semantic search not available or no data provided")
            return data[:top_k] if len(data) > top_k else data
        
        try:
            # Filter valid records that contain the field_to_match
            valid_records = [r for r in data if isinstance(r, dict) and field_to_match in r]
            
            if not valid_records:
                logger.warning(f"No valid records containing '{field_to_match}' for semantic search")
                return []
            
            # Extract the field to match from data
            field_values = [record[field_to_match] for record in valid_records]
            
            # Log the data we're searching through
            logger.info(f"\n{'='*50}\nSEMANTIC SEARCH DETAILS\n{'='*50}")
            logger.info(f"Query: '{query_text}'")
            logger.info(f"Field to match: '{field_to_match}'")
            logger.info(f"Total records to search: {len(valid_records)}")
            logger.info(f"Top {top_k} matches will be returned")
            
            # Encode the query and field values
            logger.info(f"Encoding for semantic search: {query_text}")
            query_embedding = self.sentence_model.encode(query_text)
            field_embeddings = self.sentence_model.encode(field_values)
            
            # Calculate cosine similarity
            similarities = cosine_similarity(
                query_embedding.reshape(1, -1), 
                field_embeddings
            )[0]
            
            # Get indices of top_k most similar values
            top_indices = np.argsort(similarities)[-top_k:]
            top_indices = top_indices[::-1]  # Reverse to get highest similarity first
            
            # Get the corresponding records
            top_records = [valid_records[i] for i in top_indices]
            
            # Log similarity scores for debugging
            logger.info(f"\n{'='*50}\nSEMANTIC SEARCH RESULTS\n{'='*50}")
            for i, idx in enumerate(top_indices):
                logger.info(f"Match {i+1}: Score {similarities[idx]:.4f}")
                
                # Always show the field we matched against
                logger.info(f"  {field_to_match}: {field_values[idx]}")
                
                # Show all important fields if they exist
                if 'problem' in valid_records[idx]:
                    logger.info(f"  Problem: {valid_records[idx]['problem']}")
                if 'root_cause' in valid_records[idx]:
                    logger.info(f"  Root Cause: {valid_records[idx]['root_cause']}")
                if 'area' in valid_records[idx]:
                    logger.info(f"  Area: {valid_records[idx]['area']}")
                if 'category' in valid_records[idx]:
                    logger.info(f"  Category: {valid_records[idx]['category']}")
                if 'temporary_action' in valid_records[idx]:
                    logger.info(f"  Temporary Action: {valid_records[idx]['temporary_action'][:100]}..." if len(valid_records[idx]['temporary_action']) > 100 else f"  Temporary Action: {valid_records[idx]['temporary_action']}")
                if 'preventive_action' in valid_records[idx]:
                    logger.info(f"  Preventive Action: {valid_records[idx]['preventive_action'][:100]}..." if len(valid_records[idx]['preventive_action']) > 100 else f"  Preventive Action: {valid_records[idx]['preventive_action']}")
                
                # Add separator between matches for readability
                logger.info(f"  {'-'*40}")
            logger.info(f"{'='*50}")
            
            return top_records
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return data[:top_k] if len(data) > top_k else data
    
    def get_semantic_root_cause_data(self, problem: str, area: str, category: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Get historical data for root cause suggestions with semantic filtering based on problem similarity
        
        Args:
            problem (str): The problem description to find similar cases for
            area (str): The area to filter by
            category (str): The category to filter by
            top_k (int): Number of most relevant records to return
            
        Returns:
            list: List of semantically relevant historical records for root cause suggestions
        """
        # First get basic data filtered by area and category
        basic_data = self.get_optimized_data_by_area_and_category(area, category)
        
        if not basic_data:
            logger.warning(f"No basic data found for area '{area}' and category '{category}'")
            return []
        
        # Then apply semantic filtering based on problem similarity
        return self._filter_by_semantic_similarity(problem, basic_data, 'problem', top_k)
    
    def get_semantic_action_data(self, problem: str, root_cause: str, area: str, category: str, top_k: int = 5, 
                                problem_filter_count: int = 8) -> List[Dict[str, Any]]:
        """
        Get historical data for action suggestions with sequential filtering:
        1. First filter top N problem matches
        2. Then filter those results by root cause similarity
        
        Args:
            problem (str): The problem description
            root_cause (str): The identified root cause
            area (str): The area to filter by
            category (str): The category to filter by
            top_k (int): Final number of most relevant records to return
            problem_filter_count (int): Number of problem matches to filter in first step
            
        Returns:
            list: List of semantically relevant historical records for action suggestions
        """
        # First get action data filtered by area and category
        action_data = self.get_action_data_by_area_and_category(area, category)
        
        if not action_data:
            logger.warning(f"No action data found for area '{area}' and category '{category}'")
            return []
        
        # Apply sequential semantic filtering
        logger.info(f"Searching for actions with problem: '{problem}' and root cause: '{root_cause}'")
        
        # STEP 1: Filter by problem similarity first (get top problem_filter_count matches)
        problem_matches = self._filter_by_semantic_similarity(problem, action_data, 'problem', problem_filter_count)
        logger.info(f"Step 1: Found {len(problem_matches)} matches based on problem similarity")
        
        if not problem_matches:
            logger.warning("No problem matches found, returning empty list")
            return []
        
        # STEP 2: From those problem matches, filter by root cause similarity
        final_matches = self._filter_by_semantic_similarity(root_cause, problem_matches, 'root_cause', top_k)
        logger.info(f"Step 2: Filtered to {len(final_matches)} final matches based on root cause similarity")
        
        # Log the top results
        for i, record in enumerate(final_matches[:3]):
            if 'problem' in record and 'root_cause' in record:
                logger.info(f"Top action match {i+1}:")
                logger.info(f"  Problem: {record['problem']}")
                logger.info(f"  Root Cause: {record['root_cause']}")
                if 'temporary_action' in record:
                    logger.info(f"  Temporary Action: {record['temporary_action']}")
                if 'preventive_action' in record:
                    logger.info(f"  Preventive Action: {record['preventive_action']}")
        
        return final_matches
        
    def get_all_areas(self):
        """
        Get all unique areas from the database
        
        Returns:
            list: A list of all unique areas
        """
        query = "SELECT DISTINCT area FROM gemba_issues ORDER BY area"
        
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return [r['area'] for r in result]
        except mysql.connector.Error as err:
            print(f"Error fetching areas: {err}")
            return []
