import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv('DB_PATH')

class ProgramsSeed:
    def __init__(self):
        # double degree students should choose either math or cs accordingly
        self.all_programs = {
            "Accounting and Financial Management": {
                "degree": "BAFM",
                "faculty": "Arts"
            },
            "Architectural Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Architecture": {
                "degree": "BArch",
                "faculty": "Engineering"
            },
            "Biomedical Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Biotechnology/Chartered Professional Accountancy": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Chemical Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Civil Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Climate and Environmental Change": {
                "degree": "BES",
                "faculty": "Environment"
            },
            "Computer Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Computer Science": {
                "degree": "BCS/BMath",
                "faculty": "Mathematics"
            },
            "Computing and Financial Management": {
                "degree": "BCFM",
                "faculty": "Mathematics"
            },
            "Electrical Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Environment and Business": {
                "degree": "BES",
                "faculty": "Environment"
            },
            "Environment, Resources and Sustainability": {
                "degree": "BES",
                "faculty": "Environment"
            },
            "Environmental Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Environmental Sciences": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Geography and Aviation": {
                "degree": "BES",
                "faculty": "Environment"
            },
            "Geography and Environmental Management": {
                "degree": "BES",
                "faculty": "Environment"
            },
            "Geological Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Geomatics": {
                "degree": "BES",
                "faculty": "Environment"
            },
            "Global Business and Digital Arts": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Health Sciences": {
                "degree": "BSc",
                "faculty": "Health"
            },
            "Honours Science": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Information Technology Management": {
                "degree": "BMath",
                "faculty": "Math"
            },
            "Kinesiology": {
                "degree": "BSc",
                "faculty": "Health"
            },
            "Knowledge Integration": {
                "degree": "BKI",
                "faculty": "Environment"
            },
            "Management Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Mathematics/Business Administration": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics/Chartered Professional Accountancy": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics/Financial Analysis and Risk Management": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mechanical Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Mechatronics Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Pharmacy": {
                "degree": "PharmD",
                "faculty": "Science"
            },
            "Planning": {
                "degree": "BES",
                "faculty": "Environment"
            },
            "Science and Aviation": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Science and Business": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Software Engineering": {
                "degree": "BSE",
                "faculty": "Engineering/Mathematics"
            },
            "Sustainability and Financial Management": {
                "degree": "BSFM",
                "faculty": "Environment"
            },
            "Systems Design Engineering": {
                "degree": "BASc",
                "faculty": "Engineering"
            },
            "Honours Arts - Undeclared": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Anthropology": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Classical Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Communication Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Economics": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - English Creative and Professional Writing": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - English Literature": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - English Literature and Rhetoric": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - English Rhetoric, Media, and Professional Communication": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Fine Arts Studio Practice": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Fine Arts Visual Culture": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - French": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Gender and Social Justice": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - History": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Legal Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Liberal Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Medieval Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Music": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Peace and Conflict Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Philosophy": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Political Science": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Psychology": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Religion, Culture, and Spirituality": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Sexualities, Relationships, and Families": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Social Development Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Sociology": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts - Theatre and Performance": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Undeclared": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Anthropology": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Classical Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Communication Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Economics": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - English Creative and Professional Writing": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - English Literature": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - English Literature and Rhetoric": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - English Rhetoric, Media, and Professional Communication": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Fine Arts Studio Practice": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Fine Arts Visual Culture": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - French": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Gender and Social Justice": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - History": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Legal Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Liberal Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Medieval Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Music": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Peace and Conflict Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Philosophy": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Political Science": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Psychology": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Religion, Culture, and Spirituality": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Sexualities, Relationships, and Families": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Social Development Studies": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Sociology": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Honours Arts and Business - Theatre and Performance": {
                "degree": "BA",
                "faculty": "Arts"
            },
            "Mathematics - Undeclared": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Actuarial Science": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Applied Mathematics": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Biostatistics": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Combinatorics and Optimization": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Computational Mathematics": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Data Science": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Mathematical Economics": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Mathematical Finance": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Mathematical Optimization": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Mathematical Physics": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Mathematical Studies": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Pure Mathematics": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Statistics": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Mathematics - Mathematics/Teaching": {
                "degree": "BMath",
                "faculty": "Mathematics"
            },
            "Life Sciences - Biochemistry": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Life Sciences - Biology": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Life Sciences - Biomedical Sciences": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Life Sciences - Psychology": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Physical Sciences - Biological and Medical Physics": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Physical Sciences - Chemistry": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Physical Sciences - Earth Sciences": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Physical Sciences - Materials and Nanosciences": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Physical Sciences - Mathematical Physics": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Physical Sciences - Medicinal Chemistry": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Physical Sciences - Physics": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Physical Sciences - Physics and Astronomy": {
                "degree": "BSc",
                "faculty": "Science"
            },
            "Public Health": {
                "degree": "BPH",
                "faculty": "Health"
            },
            "Recreation and Leisure Studies - Recreation, Leadership, and Health": {
                "degree": "BA",
                "faculty": "Health"
            },
            "Recreation and Leisure Studies - Sport and Recreation Management": {
                "degree": "BA",
                "faculty": "Health"
            },
            "Recreation and Leisure Studies - Therapeutic Recreation": {
                "degree": "BA",
                "faculty": "Health"
            },
        }
    
    def create_table(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DROP TABLE IF EXISTS programs')
        
        cursor.execute('''
            CREATE TABLE programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                degree TEXT NOT NULL,
                faculty TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def populate_table(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for program_name, program_info in self.all_programs.items():
            cursor.execute('''
                INSERT INTO programs (name, degree, faculty)
                VALUES (?, ?, ?)
            ''', (program_name, program_info['degree'], program_info['faculty']))
        
        conn.commit()
        conn.close()
    
    def run(self):
        self.create_table()
        self.populate_table()

def main():
    programs_seed = ProgramsSeed()
    programs_seed.run()

if __name__ == "__main__":
    main()