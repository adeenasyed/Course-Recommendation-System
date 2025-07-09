import sqlite3
from contextlib import contextmanager
import os
import json
from dotenv import load_dotenv
from typing import Dict, List, Optional, Tuple
import logging

load_dotenv()
DB_PATH = os.getenv('DB_PATH')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self._init_database()
        self.valid_programs = self._load_valid_programs()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_database(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS individual_reqs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    value TEXT NOT NULL,
                    UNIQUE(type, operator, value)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS req_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course TEXT NOT NULL,
                    parent_id INTEGER,
                    type TEXT NOT NULL,
                    individual_id INTEGER,
                    position INTEGER NOT NULL,
                    
                    FOREIGN KEY (course) REFERENCES courses(code),
                    FOREIGN KEY (parent_id) REFERENCES req_groups(id),
                    FOREIGN KEY (individual_id) REFERENCES individual_reqs(id)
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_req_groups_course ON req_groups(course)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_req_groups_parent ON req_groups(parent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_req_groups_course_parent ON req_groups(course, parent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_individual_reqs ON individual_reqs(type, operator, value)")

    def _load_valid_programs(self) -> List[str]:
        """Load valid program names from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM programs WHERE faculty LIKE '%Engineering%' ORDER BY name")
            programs = [row[0] for row in cursor.fetchall()]
            logger.info(f"Loaded {len(programs)} valid programs from database")
            return programs

    def get_available_subjects(self) -> List[str]:
        """Get list of available subjects from course_lib directory."""
        course_lib_path = os.path.join(os.path.dirname(__file__), 'course_lib')
        if not os.path.exists(course_lib_path):
            logger.warning(f"course_lib directory not found at {course_lib_path}")
            return []
        
        subjects = []
        for item in os.listdir(course_lib_path):
            item_path = os.path.join(course_lib_path, item)
            if os.path.isdir(item_path) and item != 'invalid':
                subjects.append(item)
        
        return sorted(subjects)

    def _validate_requirements_structure(self, course: str, requirements: Dict) -> bool:
        """Validate that requirements follow the expected AIPrompt format."""
        if not isinstance(requirements, dict):
            logger.warning(f"Invalid requirements for {course}: not a dictionary")
            return False
        
        # Check if requirements is null (valid case)
        if requirements is None:
            return True
        
        # Check for required operator field
        if "operator" not in requirements:
            logger.warning(f"Invalid requirements for {course}: missing 'operator' field")
            return False
        
        # Check operator value
        if requirements["operator"] not in ["AND", "OR"]:
            logger.warning(f"Invalid requirements for {course}: operator must be 'AND' or 'OR', got '{requirements['operator']}'")
            return False
        
        # Check for required conditions field
        if "conditions" not in requirements:
            logger.warning(f"Invalid requirements for {course}: missing 'conditions' field")
            return False
        
        if not isinstance(requirements["conditions"], list):
            logger.warning(f"Invalid requirements for {course}: 'conditions' must be a list")
            return False
        
        # Validate each condition
        for i, condition in enumerate(requirements["conditions"]):
            if not self._validate_condition(course, condition, f"condition[{i}]"):
                return False
        
        return True
    
    def _validate_condition(self, course: str, condition: Dict, path: str) -> bool:
        """Validate a single condition or nested group."""
        if not isinstance(condition, dict):
            logger.warning(f"Invalid {path} for {course}: not a dictionary")
            return False
        
        # Check if it's a nested group (has operator and conditions)
        if "operator" in condition and "conditions" in condition:
            if condition["operator"] not in ["AND", "OR"]:
                logger.warning(f"Invalid {path} for {course}: operator must be 'AND' or 'OR', got '{condition['operator']}'")
                return False
            
            if not isinstance(condition["conditions"], list):
                logger.warning(f"Invalid {path} for {course}: 'conditions' must be a list")
                return False
            
            # Recursively validate nested conditions
            for i, nested_condition in enumerate(condition["conditions"]):
                if not self._validate_condition(course, nested_condition, f"{path}.conditions[{i}]"):
                    return False
            
            return True
        
        # Check if it's a leaf condition (has type, operator, value)
        required_fields = ["type", "operator", "value"]
        for field in required_fields:
            if field not in condition:
                logger.warning(f"Invalid {path} for {course}: missing '{field}' field")
                return False
        
        # Validate type
        valid_types = ["PROGRAM", "LEVEL", "MINOR"]
        if condition["type"] not in valid_types:
            logger.warning(f"Invalid {path} for {course}: type must be one of {valid_types}, got '{condition['type']}'")
            return False
        
        # Validate operator based on type
        if condition["type"] == "PROGRAM":
            valid_operators = ["=", "!="]
        elif condition["type"] == "LEVEL":
            valid_operators = ["=", ">="]
        elif condition["type"] == "MINOR":
            valid_operators = ["="]
        else:
            valid_operators = []
        
        if condition["operator"] not in valid_operators:
            logger.warning(f"Invalid {path} for {course}: operator for type '{condition['type']}' must be one of {valid_operators}, got '{condition['operator']}'")
            return False
        
        # Validate value is a string
        if not isinstance(condition["value"], str):
            logger.warning(f"Invalid {path} for {course}: value must be a string, got {type(condition['value'])}")
            return False
        
        # Validate LEVEL values
        if condition["type"] == "LEVEL":
            valid_levels = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B"]
            if condition["value"] not in valid_levels:
                logger.warning(f"Invalid {path} for {course}: LEVEL value must be one of {valid_levels}, got '{condition['value']}'")
                return False
        
        # Validate PROGRAM values
        if condition["type"] == "PROGRAM":
            if condition["value"] not in self.valid_programs:
                logger.warning(f"Invalid {path} for {course}: PROGRAM value '{condition['value']}' not found in valid programs list")
                return False
        
        return True

    def load_subject_requirements(self, subject: str) -> Dict:
        """Load all course requirements for a specific subject from course_lib."""
        course_lib_path = os.path.join(os.path.dirname(__file__), 'course_lib')
        subject_path = os.path.join(course_lib_path, subject)
        
        if not os.path.exists(subject_path):
            logger.warning(f"Subject directory not found: {subject_path}")
            return {}
        
        requirements = {}
        json_files = [f for f in os.listdir(subject_path) if f.endswith('.json')]
        skipped_count = 0
        
        for json_file in json_files:
            file_path = os.path.join(subject_path, json_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'parsed_requirements' in data:
                        parsed_reqs = data['parsed_requirements']
                        
                        # Validate each course's requirements
                        valid_courses = {}
                        for course, course_requirements in parsed_reqs.items():
                            if self._validate_requirements_structure(course, course_requirements):
                                valid_courses[course] = course_requirements
                            else:
                                skipped_count += 1
                                logger.info(f"Skipping {course} due to invalid requirements structure")
                        
                        requirements.update(valid_courses)
                    else:
                        logger.warning(f"No parsed_requirements found in {json_file}")
                        skipped_count += 1
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
                skipped_count += 1
        
        logger.info(f"Loaded {len(requirements)} valid courses for subject {subject}, skipped {skipped_count} invalid courses")
        return requirements

    def store_course_requirements(self, ai_output: Dict, batch_size: int = 1000):
        if not ai_output:
            return
            
        with self.get_connection() as conn:
            processor = _BulkRequirementProcessor(conn)
            processor.process_all_courses(ai_output, batch_size)
            print(f"Successfully processed {len(ai_output)} courses")

    def process_all_subjects(self, batch_size: int = 1000):
        """Process all subjects from course_lib one at a time."""
        subjects = self.get_available_subjects()
        if not subjects:
            logger.error("No subjects found in course_lib")
            return
        
        total_processed = 0
        
        for subject in subjects:
            logger.info(f"Processing subject: {subject}")
            requirements = self.load_subject_requirements(subject)
            
            if requirements:
                self.store_course_requirements(requirements, batch_size)
                total_processed += len(requirements)
                logger.info(f"Completed processing {len(requirements)} courses for {subject}")
            else:
                logger.warning(f"No requirements found for subject {subject}")
        
        logger.info(f"Total courses processed across all subjects: {total_processed}")

class _BulkRequirementProcessor:
    def __init__(self, conn):
        self.conn = conn
        self.individual_req_cache = {}
        self._prepare_statements()
    
    def _prepare_statements(self):
        self.insert_individual_req = self.conn.prepare(
            "INSERT INTO individual_reqs (type, operator, value) VALUES (?, ?, ?)"
        ) if hasattr(self.conn, 'prepare') else None
        
        self.insert_req_group = self.conn.prepare(
            "INSERT INTO req_groups (course, parent_id, type, individual_id, position) VALUES (?, ?, ?, ?, ?)"
        ) if hasattr(self.conn, 'prepare') else None
    
    def _load_individual_reqs_cache(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, type, operator, value FROM individual_reqs")
        for req_id, req_type, operator, value in cursor.fetchall():
            self.individual_req_cache[(req_type, operator, value)] = req_id
    
    def process_all_courses(self, ai_output: Dict, batch_size: int):
        try:
            self.conn.execute("BEGIN IMMEDIATE TRANSACTION")
            self._load_individual_reqs_cache()
            
            all_individual_reqs = []
            all_req_groups = []
            
            for course, requirements in ai_output.items():
                if requirements is None:
                    continue
                    
                individual_reqs, req_groups = self._collect_course_operations(course, requirements)
                all_individual_reqs.extend(individual_reqs)
                all_req_groups.extend(req_groups)
            

            self._bulk_insert_individual_reqs(all_individual_reqs)
            self._bulk_insert_req_groups(all_req_groups, batch_size)
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Bulk processing failed: {e}")
    
    def _collect_course_operations(self, course: str, requirements: Dict) -> Tuple[List, List]:
        individual_reqs = []
        req_groups = []
        
        def collect_group(group: Dict, parent_id: Optional[int], position: int) -> int:
            group_id = len(req_groups) + 1000000
            
            group_type = group.get("operator")
            req_groups.append((course, parent_id, group_type, None, position, group_id))
            
            conditions = group.get("conditions", [])
            for i, condition in enumerate(conditions):
                if "type" in condition and "operator" in condition and "value" in condition:
                    key = (condition["type"], condition["operator"], condition["value"])
                    if key not in self.individual_req_cache:
                        individual_reqs.append(key)
                    req_groups.append((course, group_id, "CONDITION", key, i, None))
                else:
                    collect_group(condition, group_id, i)
        
        collect_group(requirements, None, 0)
        return individual_reqs, req_groups
    
    def _bulk_insert_individual_reqs(self, individual_reqs: List[Tuple]):
        unique_reqs = list(set(individual_reqs))
        
        self.conn.executemany(
            "INSERT OR IGNORE INTO individual_reqs (type, operator, value) VALUES (?, ?, ?)",
            unique_reqs
        )
        
        cursor = self.conn.cursor()
        for type, operator, value in unique_reqs:
            if (type, operator, value) not in self.individual_req_cache:
                cursor.execute(
                    "SELECT id FROM individual_reqs WHERE type = ? AND operator = ? AND value = ?",
                    (type, operator, value)
                )
                result = cursor.fetchone()
                if result:
                    self.individual_req_cache[(type, operator, value)] = result[0]
    
    def _bulk_insert_req_groups(self, req_groups: List[Tuple], batch_size: int):
        cursor = self.conn.cursor()
        temp_to_real_id = {}
        
        groups = [(course, parent_id, group_type, position, temp_id) 
                 for course, parent_id, group_type, _, position, temp_id in req_groups 
                 if temp_id is not None]
        
        individual_reqs = [(course, parent_id, individual_key, position) 
                          for course, parent_id, _, individual_key, position, temp_id in req_groups 
                          if temp_id is None and individual_key is not None]
        
        # Sort groups by roots first, then children
        # Groups with parent_id=None come first, then by temp_id order
        groups.sort(key=lambda x: (x[1] is not None, x[4]))  # false sorted before true
        
        for course, parent_temp_id, group_type, position, temp_id in groups:
            real_parent_id = temp_to_real_id.get(parent_temp_id) if parent_temp_id else None
            
            cursor.execute(
                "INSERT INTO req_groups (course, parent_id, type, individual_id, position) VALUES (?, ?, ?, ?, ?)",
                (course, real_parent_id, group_type, None, position)
            )
            
            real_id = cursor.lastrowid
            temp_to_real_id[temp_id] = real_id
        
        individual_inserts = []
        for course, parent_temp_id, individual_key, position in individual_reqs:
            individual_id = self.individual_req_cache.get(individual_key)
            
            if individual_id:
                real_parent_id = temp_to_real_id.get(parent_temp_id) if parent_temp_id else None
                individual_inserts.append((course, real_parent_id, "CONDITION", individual_id, position))
        
        if individual_inserts:
            for i in range(0, len(individual_inserts), batch_size):
                batch = individual_inserts[i:i + batch_size]
                cursor.executemany(
                    "INSERT INTO req_groups (course, parent_id, type, individual_id, position) VALUES (?, ?, ?, ?, ?)",
                    batch
                )


if __name__ == "__main__":
    db = Database()
    
    # Process all subjects from course_lib one at a time
    print("Starting to process all subjects from course_lib...")
    db.process_all_subjects()
    print("Processing complete!")