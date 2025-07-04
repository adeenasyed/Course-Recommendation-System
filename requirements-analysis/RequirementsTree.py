import sqlite3
from contextlib import contextmanager
import os
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


    def store_course_requirements(self, ai_output: Dict, batch_size: int = 1000):
        if not ai_output:
            return
            
        with self.get_connection() as conn:
            processor = _BulkRequirementProcessor(conn)
            processor.process_all_courses(ai_output, batch_size)
            print(f"Successfully processed {len(ai_output)} courses")

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