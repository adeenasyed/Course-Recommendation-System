import sqlite3
import json
import time
import requests
from typing import Optional
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

        self.prompt_template = self._update_prompt_template()
    
    def _update_prompt_template(self) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM programs WHERE faculty LIKE '%Engineering%' ORDER BY name")
        programs = [row['name'] for row in cursor.fetchall()]
        
        programs_list = ', '.join(f'"{p}"' for p in programs)
        
        template = PROMPT_TEMPLATE.replace("#programs_list#", programs_list)
        
        return template
        
    def process_single_course(self, course: str, requirements_description: str) -> Optional[str]:
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

            return response.json()["response"].strip()
        
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
        successful_count = 0
        invalid_count = 0
        failed_count = 0
        
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
                    try:
                        parsed_requirements = json.loads(result)
                        
                        output = {
                            "course": course,
                            "requirements_description": requirements_description,
                            "parsed_requirements": parsed_requirements
                        }
                        
                        dir_path = os.path.join('course_lib', subject)
                        os.makedirs(dir_path, exist_ok=True)
                        
                        file_path = os.path.join(dir_path, f"{course}.json")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(output, f, ensure_ascii=False)
                        
                        successful_count += 1
                            
                    except json.JSONDecodeError:
                        print(f"Invalid JSON for {course}")
                        
                        output = {
                            "course": course,
                            "requirements_description": requirements_description,
                            "raw_response": result,
                        }
                        
                        dir_path = os.path.join('course_lib', 'invalid')
                        os.makedirs(dir_path, exist_ok=True)

                        file_path = os.path.join(dir_path, f"{course}.json")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(output, f, ensure_ascii=False)
                        
                        invalid_count += 1
                else: 
                    failed_count += 1
                
                time.sleep(delay)
            
            print(f"Processed batch {batch_num}")
        
        print(f"Processing complete")
        print(f"Successfully processed {successful_count}/{total_courses} courses")
        print(f"Invalid JSON responses: {invalid_count}")
        print(f"Failures: {failed_count}")


if __name__ == "__main__":
    processor = RequirementsProcessor()
    processor.process_all_courses()
    processor.conn.close()