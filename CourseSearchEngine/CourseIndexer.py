import os
import json
import re
from collections import defaultdict, Counter
import sqlite3
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv('DB_PATH')

class CourseIndexer:
    def __init__(self):
        self.output_dir = "CourseSearchEngine/index"
        self.lexicon = {}
        self.inverted_index = defaultdict(dict)  # token_id -> {course_code: tf}
        self.courses = []
        self.doc_lengths = {}  # course_code -> length
        os.makedirs(self.output_dir, exist_ok=True)

    def tokenize(self, text):
        return [t for t in re.split(r'\W+', text.lower()) if t]

    def fetch_courses_from_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = "SELECT code, title, description FROM courses WHERE subject in ('AE', 'ARCH', 'BME', 'CHE', 'ECE', 'ENVE', 'GENE', 'GEOE', 'ME', 'MSE', 'MTE', 'NE', 'SE', 'SYDE')"
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        for code, title, description in results:
            self.courses.append({
                'code': code,
                'title': title,
                'description': description
            })

    def build(self):
        for course in self.courses:
            course_code = course['code']
            tokens = self.tokenize(course['title'] + ' ' + course['description'])
            self.doc_lengths[course_code] = len(tokens)
            token_counts = Counter(tokens)
            for token, count in token_counts.items():
                if token not in self.lexicon:
                    self.lexicon[token] = len(self.lexicon) + 1
                token_id = self.lexicon[token]
                self.inverted_index[token_id][course_code] = count
        self.save()

    def save(self):
        # Save lexicon
        with open(os.path.join(self.output_dir, 'lexicon.json'), 'w') as f:
            json.dump(self.lexicon, f, indent=2)
        # Save inverted index
        with open(os.path.join(self.output_dir, 'inverted_index.json'), 'w') as f:
            json.dump(self.inverted_index, f, indent=2)
        # Save course metadata
        with open(os.path.join(self.output_dir, 'courses.json'), 'w') as f:
            json.dump(self.courses, f, indent=2)
        # Save document lengths
        with open(os.path.join(self.output_dir, 'doc_lengths.json'), 'w') as f:
            json.dump(self.doc_lengths, f, indent=2)

if __name__ == "__main__":
    indexer = CourseIndexer()
    indexer.fetch_courses_from_db()
    indexer.build()
    print("Course index built and saved to index/") 