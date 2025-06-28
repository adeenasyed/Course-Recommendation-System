"""
This script uses Waterloo's Open Data API to retrieve subjects and store them in a SQLite db file.

IN SQLITE WE TRUST

API Documentation: 
https://uwaterloo.ca/api/
https://openapi.data.uwaterloo.ca/api-docs/index.html
"""

from typing import List
import requests
import sqlite3
from contextlib import contextmanager
import os
from dotenv import load_dotenv
import logging

load_dotenv()
API_KEY = os.getenv('API_KEY')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "waterloo_courses.db"):
        self.db_path = db_path
        self.create_table()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def create_table(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            conn.commit()
            logger.info("Created subjects table")
    
    def insert_subjects(self, subjects: List[dict]):
        with self.get_connection() as conn:
            try:
                subject_batch = [
                    (
                        subject.get('code', ''),
                        subject.get('description', '')
                    )
                    for subject in subjects
                ]
                
                conn.executemany("""
                    INSERT OR REPLACE INTO subjects 
                    (code, name)
                    VALUES (?, ?)
                """, subject_batch)
                conn.commit()
                logger.info(f"Inserted {len(subjects)} subjects")
            except sqlite3.Error as e:
                logger.error(f"Error inserting subjects: {e}")

class DataFetcher:
    def __init__(self):
        self.base_url = "https://openapi.data.uwaterloo.ca/v3"
        
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': API_KEY
        })
    
    def get_subjects(self) -> List[dict]:
        url = f"{self.base_url}/Subjects"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                logger.info(f"Retrieved {len(data)} subjects")
                return data
            else:
                return []
            
        except Exception as e:
            logger.error(f"Error fetching subjects: {e}")
            return []
    
    def fetch_and_store_subjects(self, db: Database):
        subjects = self.get_subjects()
        
        if subjects:
            db.insert_subjects(subjects)
        
        logger.info(f"Total subjects stored in database: {len(subjects)}")


def main():
    db = Database()
    dataFetcher = DataFetcher()
    
    dataFetcher.fetch_and_store_subjects(db)
    
    print(f"\nDatabase saved as 'waterloo_courses.db'")


if __name__ == "__main__":
    main()