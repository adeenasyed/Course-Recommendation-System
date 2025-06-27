"""
UW Course Data Fetching
=======================

This script uses UW-Open-Data-API to retrieve course information and store it in a SQLite db file.

IN SQLITE WE TRUST

API Documentation: 
https://github.com/uWaterloo/api-documentation
https://github.com/zainh96/UW-Open-Data-API
"""

import requests
import time
from typing import List
from dataclasses import dataclass
import logging
import sqlite3
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Course:
    subject: str
    catalog_number: str
    title: str
    description: str = ""

    # raw text from API
    prerequisites_raw: str = ""
    antirequisites_raw: str = ""
    corequisites_raw: str = ""
    cross_listed_raw: str = ""
    
    # parsed lists
    # prerequisites: List[str] = None
    # antirequisites: List[str] = None
    # corequisites: List[str] = None
    # cross_listed: List[str] = None

    units: float = 0.0
    terms_offered: List[str] = None
    held_with: str = ""
    note: str = ""
    last_updated: str = ""
    url: str = ""
    full_code: str = ""
    
    def __post_init__(self):
        if self.terms_offered is None:
            self.terms_offered = []
        
        self.full_code = f"{self.subject} {self.catalog_number}"

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
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    catalog_number TEXT NOT NULL,
                    full_code TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    prerequisites_raw TEXT,
                    antirequisites_raw TEXT,
                    corequisites_raw TEXT,
                    cross_listed_raw TEXT,
                    units REAL,
                    terms_offered TEXT,
                    held_with TEXT,
                    note TEXT,
                    last_updated TEXT,
                    url TEXT,
                    UNIQUE(subject, catalog_number)
                )
            """)
            conn.commit()
            logger.info("Database table created")
    
    def insert_course(self, course: Course):
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO courses 
                    (subject, catalog_number, full_code, title, description,
                     prerequisites_raw, antirequisites_raw, corequisites_raw, 
                     cross_listed_raw, units, terms_offered, held_with, note, last_updated, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    course.subject,
                    course.catalog_number,
                    course.full_code,
                    course.title,
                    course.description,
                    course.prerequisites_raw,
                    course.antirequisites_raw,
                    course.corequisites_raw,
                    course.cross_listed_raw,
                    course.units,
                    ','.join(course.terms_offered),
                    course.held_with,
                    course.note,
                    course.last_updated,
                    course.url
                ))
                conn.commit()
                logger.info(f"Inserted course {course.full_code}")
            except sqlite3.Error as e:
                logger.error(f"Error inserting course {course.full_code}: {e}")
    
    def insert_course_batch(self, courses: List[Course]):
        with self.get_connection() as conn:
            try:
                course_batch = [
                    (
                        course.subject,
                        course.catalog_number,
                        course.full_code,
                        course.title,
                        course.description,
                        course.prerequisites_raw,
                        course.antirequisites_raw,
                        course.corequisites_raw,
                        course.cross_listed_raw,
                        course.units,
                        ','.join(course.terms_offered),
                        course.held_with,
                        course.note,
                        course.last_updated,
                        course.url
                    )
                    for course in courses
                ]
                
                conn.executemany("""
                    INSERT OR REPLACE INTO courses 
                    (subject, catalog_number, full_code, title, description,
                     prerequisites_raw, antirequisites_raw, corequisites_raw, 
                     cross_listed_raw, units, terms_offered, held_with, note, last_updated, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, course_batch)
                conn.commit()
                logger.info(f"Inserted {len(courses)} courses")
            except sqlite3.Error as e:
                logger.error(f"Error inserting course batch: {e}")


class DataFetching:
    def __init__(self):
        self.base_url = "https://api.uwaterloo.ca/v2"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UW-Course-Recommender/1.0'
        })
    
    def get_subjects(self) -> List[str]:
        url = f"{self.base_url}/codes/subjects.json"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('meta', {}).get('status') == 200 and 'data' in data:
                subjects = [item['subject'] for item in data['data']]
                logger.info(f"Retrieved {len(subjects)} subjects")
                return subjects
            else:
                logger.error(f"API error: {data.get('meta', {})}")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching subjects: {e}")
            return []
    
    def get_courses_for_subject(self, subject: str) -> List[Course]:
        url = f"{self.base_url}/courses/{subject}.json"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            courses = []
            if data.get('meta', {}).get('status') == 200 and 'data' in data:
                for course_data in data['data']:
                    course = Course(
                        subject=course_data.get('subject', ''),
                        catalog_number=course_data.get('catalog_number', ''),
                        title=course_data.get('title', ''),
                        description=course_data.get('description', ''),
                        prerequisites_raw=course_data.get('prerequisites', ''),
                        antirequisites_raw=course_data.get('antirequisites', ''),
                        corequisites_raw=course_data.get('corequisites', ''),
                        cross_listed_raw=course_data.get('crosslistings', ''),
                        units=float(course_data.get('units', 0)),
                        terms_offered=course_data.get('terms', []),
                        held_with=course_data.get('held_with', ''),
                        note=course_data.get('note', ''),
                        last_updated=course_data.get('calendar_year', ''),
                        url=course_data.get('url', '')
                    )
                    courses.append(course)
            
            logger.info(f"Retrieved {len(courses)} courses for {subject}")
            return courses
            
        except Exception as e:
            logger.error(f"Error fetching courses for {subject}: {e}")
            return []
    
    def fetch_and_store_courses(self, db: Database):
        subjects = self.get_subjects()
        logger.info(f"Fetching courses for ALL subjects...")
        
        total_courses = 0
        
        for subject in subjects:
            courses = self.get_courses_for_subject(subject)
            if courses:
                db.insert_course_batch(courses)
                total_courses += len(courses)
            
            time.sleep(0.1)
        
        logger.info(f"Total courses stored in database: {total_courses}")


def main():
    db = Database()
    dataFetching = DataFetching()
    
    dataFetching.fetch_and_store_courses(db)
    
    print(f"\nDatabase saved as 'waterloo_courses.db'")


if __name__ == "__main__":
    main()