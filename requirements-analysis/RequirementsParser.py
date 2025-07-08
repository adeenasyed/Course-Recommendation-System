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
                print(f"Error processing JSON for {course}")
                print(f"Raw response:\n{output}")
                return None
        
        except Exception as e:
            print(f"Error processing {course}: {str(e)}")
            return None
    
    def process_all_courses(self, output_file: str = "parsed_requirements.json", batch_size: int = 20, delay: float = 0.1):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT code, requirements_description 
            FROM courses 
            WHERE requirements_description IS NOT NULL
            AND SUBJECT IN ('AE', 'ARCH', 'BME', 'CHE', 'ECE', 'ENVE', 'GENE', 'GEOE', 'ME', 'MSE', 'MTE', 'NE', 'SE', 'SYDE') 
            ORDER BY code
        """)
        
        all_courses = cursor.fetchall()
        total_courses = len(all_courses)
        
        all_results = {}
        processed_count = 0
        successful_count = 0
        
        for i in range(0, total_courses, batch_size):
            batch = all_courses[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_courses + batch_size - 1) // batch_size
            
            print(f"\nProcessing batch {batch_num}/{total_batches}, courses {i+1}-{min(i+batch_size, total_courses)}")
            
            batch_results = {}
            
            for row in batch:
                course = row['code']
                requirements_description = row['requirements_description']
                
                result = self.process_single_course(course, requirements_description)
                
                if result:
                    batch_results.update(result)
                    successful_count += 1
                
                processed_count += 1
                
                time.sleep(delay)
            
            all_results.update(batch_results)
            
            print(f"Processed batch {batch_num}.")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False)
        
        print(f"\nProcessing complete")
        print(f"Successfully processed {successful_count}/{processed_count} courses")
        print(f"Final results saved to {output_file}")
        
        return all_results


if __name__ == "__main__":
    processor = RequirementsProcessor()
    
    try:
        results = processor.process_all_courses()
        print(f"Processed {len(results)} courses")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        processor.conn.close()