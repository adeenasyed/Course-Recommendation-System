import sqlite3
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Set, Tuple
import logging

load_dotenv()
DB_PATH = os.getenv('DB_PATH')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RequirementsTreeTraveller:
    def __init__(self):
        self.valid_programs = self._load_valid_programs()
        self.valid_levels = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B"]
        self.level_to_term = {
            "1A": 1, "1B": 2, "2A": 3, "2B": 4, 
            "3A": 5, "3B": 6, "4A": 7, "4B": 8
        }
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        try:
            yield conn
        finally:
            conn.close()
    
    def _load_valid_programs(self) -> List[str]:
        """Load valid program names from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM programs WHERE faculty LIKE '%Engineering%' ORDER BY name")
            programs = [row[0] for row in cursor.fetchall()]
            # logger.info(f"Loaded {len(programs)} valid programs from database")
            return programs
    
    def get_available_courses(self, program: str, term: str, minor: Optional[str] = None) -> List[str]:
        """
        Get all courses that a person can take based on their program, term (e.g. '2A'), and optional minor.
        
        Args:
            program: The person's program name (e.g., "Computer Engineering")
            term: The current level string (e.g., '2A', '3B', etc.)
            minor: Optional minor name (e.g., "Mechatronics")
        
        Returns:
            List of course codes that the person can take
        """
        if not self._validate_inputs(program, term, minor):
            return []
        
        level = term  # Use the input term string directly as the level
        
        with self.get_connection() as conn:
            courses_with_reqs = self._get_courses_with_requirements(conn)
            available_courses = []
            
            for course in courses_with_reqs:
                can_take = self._can_take_course(conn, course, program, level, minor)
                if can_take:
                    available_courses.append(course)
            
            # logger.info(f"Found {len(available_courses)} available courses for {program} student in term {term} (level {level})")
            # if minor:
            #     logger.info(f"Minor: {minor}")
            
            return sorted(available_courses)
    
    def _validate_inputs(self, program: str, term: str, minor: Optional[str]) -> bool:
        """Validate input parameters."""
        # Case-insensitive program matching
        if not isinstance(program, str) or not any(program.lower() == p.lower() for p in self.valid_programs):
            logger.error(f"Program must be one of {self.valid_programs}")
            return False
        
        if not isinstance(term, str) or term not in self.valid_levels:
            logger.error(f"Term must be one of {self.valid_levels}'")
            return False
        
        if minor is not None and (not isinstance(minor, str) or not minor.strip()):
            logger.error("Minor must be a non-empty string")
            return False
        
        return True
    
    
    def _get_courses_with_requirements(self, conn) -> List[str]:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code
            FROM courses
            WHERE SUBJECT IN ('AE', 'ARCH', 'BME', 'CHE', 'ECE', 'ENVE', 'GENE', 'GEOE', 'ME', 'MSE', 'MTE', 'NE', 'SE', 'SYDE') 
            ORDER BY code
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def _can_take_course(self, conn, course: str, program: str, level: str, minor: Optional[str]) -> bool:
        root_group = self._get_root_requirement_group(conn, course)
        if not root_group:
            return False
        return self._evaluate_requirement_group(conn, root_group, program, level, minor)
    
    def _get_root_requirement_group(self, conn, course: str) -> Optional[Dict]:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, type, individual_id, position
            FROM req_groups 
            WHERE course = ? AND parent_id IS NULL
            ORDER BY position
        """, (course,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': row[0],
            'type': row[1],
            'individual_id': row[2],
            'position': row[3]
        }
    
    def _evaluate_requirement_group(self, conn, group: Dict, program: str, level: str, minor: Optional[str]) -> bool:
        if group['type'] == 'CONDITION':
            return self._evaluate_condition(conn, group['individual_id'], program, level, minor)
        else:
            children = self._get_child_groups(conn, group['id'])
            if not children:
                return True
            if children[0]['type'] == 'CONDITION':
                individual_req = self._get_individual_requirement(conn, children[0]['individual_id'])
                if not individual_req:
                    return True
                operator = "OR"
            else:
                operator = group['type']
            if operator == "AND":
                return all(self._evaluate_requirement_group(conn, child, program, level, minor) 
                          for child in children)
            else:
                return any(self._evaluate_requirement_group(conn, child, program, level, minor) 
                          for child in children)
    
    def _get_child_groups(self, conn, parent_id: int) -> List[Dict]:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, type, individual_id, position
            FROM req_groups 
            WHERE parent_id = ?
            ORDER BY position
        """, (parent_id,))
        return [
            {
                'id': row[0],
                'type': row[1],
                'individual_id': row[2],
                'position': row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def _get_individual_requirement(self, conn, individual_id: int) -> Optional[Dict]:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type, operator, value
            FROM individual_reqs 
            WHERE id = ?
        """, (individual_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'type': row[0],
            'operator': row[1],
            'value': row[2]
        }
    
    def _evaluate_condition(self, conn, individual_id: int, program: str, level: str, minor: Optional[str]) -> bool:
        req = self._get_individual_requirement(conn, individual_id)
        if not req:
            return False
        req_type = req['type']
        operator = req['operator']
        value = req['value']
        if req_type == "PROGRAM":
            if operator == "=":
                return program == value
            elif operator == "!=":
                return program != value
            else:
                logger.warning(f"Unknown operator '{operator}' for PROGRAM type")
                return False
        elif req_type == "LEVEL":
            if operator == "=":
                return level == value
            elif operator == ">=":
                return self._level_greater_equal(level, value)
            else:
                logger.warning(f"Unknown operator '{operator}' for LEVEL type")
                return False
        elif req_type == "MINOR":
            if operator == "=":
                return minor == value
            else:
                logger.warning(f"Unknown operator '{operator}' for MINOR type")
                return False
        else:
            logger.warning(f"Unknown requirement type: {req_type}")
            return False
    
    def _level_greater_equal(self, current_level: str, required_level: str) -> bool:
        current_term = self.level_to_term.get(current_level, 0)
        required_term = self.level_to_term.get(required_level, 0)
        return current_term >= required_term
    
    def get_course_requirements(self, course: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            root_group = self._get_root_requirement_group(conn, course)
            if not root_group:
                return None
            return self._build_requirements_tree(conn, root_group)
    
    def _build_requirements_tree(self, conn, group: Dict) -> Dict:
        if group['type'] == 'CONDITION':
            req = self._get_individual_requirement(conn, group['individual_id'])
            if req:
                return {
                    'type': req['type'],
                    'operator': req['operator'],
                    'value': req['value']
                }
            return None
        children = self._get_child_groups(conn, group['id'])
        if not children:
            return None
        operator = "OR" if group['type'] in ['AND', 'OR'] else group['type']
        conditions = []
        for child in children:
            child_tree = self._build_requirements_tree(conn, child)
            if child_tree:
                conditions.append(child_tree)
        if not conditions:
            return None
        return {
            'operator': operator,
            'conditions': conditions
        }
