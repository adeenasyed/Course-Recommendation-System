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
    title: str
    description: str
    component: str
    grading_basis: str
    requirements_description: str # PARSE THIS INTO LISTS OF PREREQS, ANTIREQS, AND COREQS
    academic_career: str
    code: str = ""
    is_pass_fail: int = 0
    
    def __post_init__(self):
        self.code = f"{self.subject} {self.catalog_number}"
        self.is_pass_fail = self.grading_basis in ["CNC", "NGP", "CNT", "CNW", "CNP", "DRN", "CUR"]

class Database:
    def __init__(self, db_path: str = "course_recommendation_system.db"):
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
                    code TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    catalog_number TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    component TEXT NOT NULL,
                    grading_basis TEXT NOT NULL,
                    is_pass_fail INTEGER DEFAULT 0,
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
                        course.code,
                        course.subject,
                        course.catalog_number,
                        course.title,
                        course.description if course.description else None,
                        course.component,
                        course.grading_basis,
                        course.is_pass_fail,
                        course.requirements_description if course.requirements_description else None,
                    )
                    for course in courses
                ]
                
                conn.executemany("""
                    INSERT INTO courses 
                    (code, subject, catalog_number, title, description, component, grading_basis, is_pass_fail, requirements_description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, course_batch)
                conn.commit()
                logger.info(f"Inserted {len(courses)} courses")
            except sqlite3.Error as e:
                logger.error(f"Error inserting courses: {e}")

class Filter:
    @staticmethod
    def is_graduate_course(course: Course) -> bool:
        return course.academic_career == "GRD"
    
    @staticmethod
    def is_capstone_course(course: Course) -> bool:
        title_lower = course.title.lower()
        return "capstone" in title_lower or "design project" in title_lower
    
    @staticmethod
    def is_excluded_subject(course: Course) -> bool:
        return course.subject in ["PD", "WKRPT", "COOP"]
    
    @staticmethod
    def is_non_credit_course(course: Course) -> bool:
        return course.grading_basis in ["NON", "XTR", "NGD"]
    
    @staticmethod
    def filter_courses(courses: List[Course]) -> List[Course]:
        filtered_courses = []

        for course in courses:
            if Filter.is_graduate_course(course):
                continue
                
            if Filter.is_capstone_course(course):
                continue
                
            if Filter.is_excluded_subject(course):
                continue
                
            if Filter.is_non_credit_course(course):
                continue
            
            filtered_courses.append(course)
        
        return filtered_courses

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
                    course = Course(
                        subject=course_data.get('subjectCode', ''),
                        catalog_number=course_data.get('catalogNumber', ''),
                        title=course_data.get('title', ''),
                        description=course_data.get('description', ''),
                        component=course_data.get('courseComponentCode', ''),
                        grading_basis=course_data.get('gradingBasis', ''),
                        requirements_description=course_data.get('requirementsDescription', ''),
                        academic_career=course_data.get('associatedAcademicCareer', ''),
                    )
                    courses.append(course)
            
            filtered_courses = Filter.filter_courses(courses)

            logger.info(f"Retrieved {len(filtered_courses)} courses for term {term_name} ({term_id})")

            return filtered_courses
        
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