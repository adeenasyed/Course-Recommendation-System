"""
This script uses Waterloo's Open Data API to retrieve course information and store it in a SQLite db file.

IN SQLITE WE TRUST

API Documentation: 
https://uwaterloo.ca/api/
https://openapi.data.uwaterloo.ca/api-docs/index.html
"""

from typing import List
import requests
from dataclasses import dataclass
import sqlite3
from contextlib import contextmanager
import os
from dotenv import load_dotenv
import logging

load_dotenv()
API_KEY = os.getenv('API_KEY')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Course:
    subject: str
    catalog_number: str
    academic_career: str
    title: str
    description: str = ""
    grading_basis: str = ""
    component: str = ""
    enrollment_consent_required: int = 0
    requirements_description: str = "" # PARSE THIS INTO LISTS OF PREREQS, ANTIREQS, AND COREQS
    full_code: str = ""
    
    def __post_init__(self):
        self.full_code = f"{self.subject} {self.catalog_number}"

class Database:
    def __init__(self, db_path: str = "waterloo_courses.db"):
        self.db_path = db_path
        self.create_tables()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def create_tables(self):
        with self.get_connection() as conn:     
            conn.execute("""
                CREATE TABLE IF NOT EXISTS terms (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    insertion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("DROP TABLE IF EXISTS courses")    
            conn.execute("""
                CREATE TABLE courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    catalog_number TEXT NOT NULL,
                    full_code TEXT UNIQUE NOT NULL,
                    academic_career TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    grading_basis TEXT NOT NULL,
                    component TEXT NOT NULL,
                    enrollment_consent_required INTEGER DEFAULT 0,
                    requirements_description TEXT,
                    UNIQUE(subject, catalog_number)
                )
            """)

            conn.commit()
            logger.info("Created terms and courses tables")
    
    def insert_term(self, id: int, name: str):
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO terms 
                    (id, name)
                    VALUES (?, ?)
                """, (int(id), name))
                conn.commit()
                logger.info(f"Inserted term {name} ({id})")
            except sqlite3.Error as e:
                logger.error(f"Error inserting term: {e}")
    
    def insert_course_batch(self, courses: List[Course]):
        with self.get_connection() as conn:
            try:
                course_batch = [
                    (
                        course.subject,
                        course.catalog_number,
                        course.full_code,
                        course.academic_career,
                        course.title,
                        course.description,
                        course.grading_basis,
                        course.component,
                        course.enrollment_consent_required,
                        course.requirements_description or ""
                    )
                    for course in courses
                ]
                
                conn.executemany("""
                    INSERT INTO courses 
                    (subject, catalog_number, full_code, academic_career, title, description,
                    grading_basis, component, enrollment_consent_required, requirements_description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, course_batch)
                conn.commit()
                logger.info(f"Inserted {len(courses)} courses")
            except sqlite3.Error as e:
                logger.error(f"Error inserting courses: {e}")

class DataFetcher:
    def __init__(self):
        self.base_url = "https://openapi.data.uwaterloo.ca/v3"
        
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': API_KEY
        })

    def get_upcoming_term(self):
        terms_url = f"{self.base_url}/Terms"
        current_term_url = f"{terms_url}/current"

        try: 
            current_term_response = self.session.get(current_term_url, timeout=30)
            current_term_response.raise_for_status()
            current_term = current_term_response.json()
        
            name_parts = current_term['name'].split()
            season = name_parts[0]
            year = int(name_parts[1])
        
            if season == "Winter":
                next_season, next_year = "Spring", year
            elif season == "Spring":
                next_season, next_year = "Fall", year
            elif season == "Fall":
                next_season, next_year = "Winter", year + 1
            
            next_name = f"{next_season} {next_year}"
        
            terms_response = self.session.get(terms_url, timeout=30)
            terms_response.raise_for_status()
            all_terms = terms_response.json()

            for term in all_terms:
                if term['name'] == next_name:
                    return term['termCode'], term['name']
            
            raise ValueError(f"Unable to find upcoming term {next_name}")
        
        except Exception as e:
            logger.error(f"Error fetching upcoming term: {e}")
            raise

    
    def get_courses_for_term(self, term_id: int, term_name: str) -> List[Course]:
        url = f"{self.base_url}/Courses/{term_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            courses = []
            if isinstance(data, list):
                for course_data in data:
                    consent_desc = course_data.get('enrollConsentDescription', '')
                    consent_req = 0 if consent_desc == "No Consent Required" else 1
                    
                    course = Course(
                        subject=course_data.get('subjectCode', ''),
                        catalog_number=course_data.get('catalogNumber', ''),
                        title=course_data.get('title', ''),
                        description=course_data.get('description', ''),
                        academic_career=course_data.get('associatedAcademicCareer', ''),
                        grading_basis=course_data.get('gradingBasis', ''),
                        component=course_data.get('courseComponentCode', ''),
                        enrollment_consent_required=consent_req,
                        requirements_description=course_data.get('requirementsDescription', '')
                    )
                    courses.append(course)
            
            logger.info(f"Retrieved {len(courses)} courses for term {term_name} ({term_id})")
            return courses
        
        except Exception as e:
            logger.error(f"Error fetching courses for term {term_name} ({term_id}): {e}")
            raise


def main():
    db = Database()
    dataFetcher = DataFetcher()
    
    try:
        term_id, term_name = dataFetcher.get_upcoming_term()
        db.insert_term(term_id, term_name)
        
        courses = dataFetcher.get_courses_for_term(term_id, term_name)
        if courses:
            db.insert_course_batch(courses)
        
    except Exception as e:
        logger.error(f"Failed to fetch and store data: {e}")
        return


if __name__ == "__main__":
    main()