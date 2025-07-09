import os
import json
import math
from collections import defaultdict
from .CourseIndexer import CourseIndexer

class CourseSearcher:
    def __init__(self, index_dir="CourseSearchEngine/index"):
        self.index_dir = index_dir
        self.lexicon = self._load_json('lexicon.json')
        self.inverted_index = self._load_json('inverted_index.json')
        self.doc_lengths = self._load_json('doc_lengths.json')
        self.courses = self._load_json('courses.json')
        self.N = len(self.doc_lengths)
        self.avg_doc_length = sum(self.doc_lengths.values()) / self.N if self.N > 0 else 0
        self.tokenizer = CourseIndexer().tokenize

    def _load_json(self, filename):
        path = os.path.join(self.index_dir, filename)
        with open(path, 'r') as f:
            data = json.load(f)
        # doc_lengths keys may be str, convert to int if needed
        if filename == 'doc_lengths.json':
            return {k: int(v) for k, v in data.items()}
        return data

    def search(self, query, eligible_course_codes=None, top_n=10):
        tokens = self.tokenizer(query)
        token_ids = [str(self.lexicon[token]) for token in tokens if token in self.lexicon]
        scores = defaultdict(float)
        k1 = 1.5
        b = 0.75
        for token_id in token_ids:
            postings = self.inverted_index.get(token_id, {})
            df = len(postings)
            if df == 0:
                continue
            idf = math.log((self.N - df + 0.5) / (df + 0.5) + 1)
            for course_code, tf in postings.items():
                if eligible_course_codes and course_code not in eligible_course_codes:
                    continue
                dl = self.doc_lengths[course_code]
                tf = int(tf)
                score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / self.avg_doc_length))
                scores[course_code] += score
        # Sort and get top N
        top_courses = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        # Map course_code to metadata
        course_map = {c['code']: c for c in self.courses}
        results = []
        for code, score in top_courses:
            course = course_map.get(code, {'code': code, 'title': '', 'description': ''})
            results.append({
                'code': code,
                'title': course.get('title', ''),
                'description': course.get('description', ''),
                'score': score
            })
        return results

if __name__ == "__main__":
    searcher = CourseSearcher()
    query = input("Enter your course search query: ")
    results = searcher.search(query)
    print("\nTop results:")
    for i, course in enumerate(results, 1):
        print(f"{i}. {course['code']}: {course['title']}\n   {course['description']}\n   Score: {course['score']:.4f}\n") 