import sqlite3
import json
import re
import time
import requests
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
from AIPrompt import PROMPT_TEMPLATE

load_dotenv()
DB_PATH = os.getenv('DB_PATH')

class RequirementsProcessor:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

        self.model = "llama3.1:8b"
        self.base_url = "http://localhost:11434"

        self.valid_programs = self._load_valid_values()
        self.prompt_template = self._update_prompt_template()
    
    def _load_valid_values(self) -> tuple[List[str], List[str]]:
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT DISTINCT name FROM programs WHERE faculty LIKE '%Engineering%' ORDER BY name")
        programs = [row['name'] for row in cursor.fetchall()]

        return programs
    
    def _update_prompt_template(self) -> str:
        programs_list = ', '.join(f'"{p}"' for p in self.valid_programs)
        
        template = PROMPT_TEMPLATE.replace("#programs_list#", programs_list)
        
        return template

        
    def process_single_course(self, course: str, requirements_description: str) -> Optional[Dict]:
        prompt = self.prompt_template.replace("#course#", course).replace("#requirements_description#", requirements_description)
        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 200,
                    "top_p": 0.5,
                    "repeat_penalty": 1.2,
                }
            }
            
            response = requests.post(f"{self.base_url}/api/generate", json=data, timeout=30)
            response.raise_for_status()
            
            output = response.json()["response"].strip()
            
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return output
        
        except Exception as e:
            print(f"Error processing {course}: {str(e)}")
            return None
    
    def process_all_courses(self, batch_size: int = 20, delay: float = 0.1):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT code, requirements_description, subject
            FROM courses 
            WHERE requirements_description IS NOT NULL
            AND SUBJECT IN ('AE', 'ARCH', 'BME', 'CHE', 'ECE', 'ENVE', 'GENE', 'GEOE', 'ME', 'MSE', 'MTE', 'NE', 'SE', 'SYDE') 
            ORDER BY code
        """)
        
        all_courses = cursor.fetchall()
        total_courses = len(all_courses)
        
        processed_count = 0
        successful_count = 0
        invalid_jsons = []
        
        for i in range(0, total_courses, batch_size):
            batch = all_courses[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_courses + batch_size - 1) // batch_size
            
            print(f"\nProcessing batch {batch_num}/{total_batches}, courses {i+1}-{min(i+batch_size, total_courses)}")
            
            for row in batch:
                course = row['code']
                requirements_description = row['requirements_description']
                subject = row['subject']
                
                result = self.process_single_course(course, requirements_description)
                
                if result:
                    # Create directory if it doesn't exist
                    dir_path = os.path.join('course_lib', subject)
                    os.makedirs(dir_path, exist_ok=True)
                    # Save to file
                    file_path = os.path.join(dir_path, f"{course}.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False)
                    successful_count += 1
                else:
                    # Create directory if it doesn't exist
                    dir_path = os.path.join('course_lib', 'invalid')
                    os.makedirs(dir_path, exist_ok=True)
                    # Save to file
                    file_path = os.path.join(dir_path, f"{course}.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False)
                    invalid_jsons.append(course)
                
                processed_count += 1
                
                time.sleep(delay)
            
            print(f"Processed batch {batch_num}.")
        
        print(f"\nProcessing complete")
        print(f"Successfully processed {successful_count}/{processed_count} courses")
        
        return successful_count


if __name__ == "__main__":
    processor = RequirementsProcessor()
    
    try:
        results = processor.process_all_courses()
        print(f"Processed {results} courses")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        processor.conn.close()