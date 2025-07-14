import os
import json
import math
import re
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
        
        # Enhanced search parameters
        self.k1 = 1.2  # BM25 parameter
        self.b = 0.75  # BM25 parameter
        self.title_weight = 3.0  # Weight for title matches
        self.description_weight = 1.0  # Weight for description matches
        
        # Common course-related terms for query expansion (shortened for engineering context)
        self.course_synonyms = {
            'programming': ['coding', 'software', 'development'],
            'calculus': ['math', 'mathematics', 'derivatives', 'integration'],
            'mechanics': ['physics', 'dynamics', 'statics', 'forces'],
            'design': ['architecture', 'planning', 'modeling'],
            'analysis': ['evaluation', 'assessment'],
            'systems': ['system', 'infrastructure', 'network'],
            'engineering': ['technical', 'applied'],
            'data': ['statistics', 'database'],
            'machine': ['automation', 'robotics'],
            'ai': ['artificial intelligence', 'machine learning'],
            'software': ['programming', 'development'],
            'hardware': ['electronics', 'circuits'],
            'network': ['communication', 'connectivity'],
            'database': ['data', 'storage'],
            'algorithm': ['computation', 'logic'],
            'structure': ['structural', 'framework'],
            'material': ['materials', 'composition'],
            'energy': ['power', 'electrical', 'thermal'],
            'fluid': ['hydraulics', 'flow'],
            'thermal': ['heat', 'thermodynamics'],
            'control': ['automation', 'regulation'],
            'signal': ['signals', 'processing'],
            'circuit': ['electronics', 'electrical'],
            'digital': ['computer', 'binary'],
            'robotics': ['automation', 'mechanical'],
            'biomedical': ['medical', 'health'],
            'environmental': ['ecology', 'sustainability'],
            'chemical': ['chemistry', 'reactions'],
            'civil': ['infrastructure', 'construction'],
            'electrical': ['electronics', 'power'],
            'mechanical': ['machines', 'dynamics'],
            'computer': ['computing', 'software', 'hardware'],
            'management': ['business', 'leadership'],
            'economics': ['finance', 'market'],
            'statistics': ['probability', 'data'],
            'optimization': ['efficiency', 'minimization'],
            'simulation': ['modeling', 'virtual'],
            'security': ['cybersecurity', 'protection'],
            'project': ['planning', 'coordination'],
            'research': ['investigation', 'study'],
        }

    def _load_json(self, filename):
        path = os.path.join(self.index_dir, filename)
        with open(path, 'r') as f:
            data = json.load(f)
        # doc_lengths keys may be str, convert to int if needed
        if filename == 'doc_lengths.json':
            return {k: int(v) for k, v in data.items()}
        return data

    def _expand_query(self, tokens):
        """Expand query with synonyms and related terms"""
        expanded_tokens = set(tokens)
        
        for token in tokens:
            # Add synonyms
            if token in self.course_synonyms:
                expanded_tokens.update(self.course_synonyms[token])
            
            # Add plural/singular forms
            if token.endswith('s'):
                expanded_tokens.add(token[:-1])
            else:
                expanded_tokens.add(token + 's')
            
            # Add common abbreviations
            if token == 'artificial':
                expanded_tokens.add('ai')
            elif token == 'intelligence':
                expanded_tokens.add('ai')
            elif token == 'machine':
                expanded_tokens.add('ml')
            elif token == 'learning':
                expanded_tokens.add('ml')
        
        return list(expanded_tokens)

    def _extract_course_code(self, query):
        """Extract potential course codes from query (e.g., CS 241, MATH 237)"""
        # Pattern for course codes like "CS 241", "MATH 237", "ECE 250"
        course_code_pattern = r'\b[A-Z]{2,4}\s+\d{3,4}\b'
        matches = re.findall(course_code_pattern, query.upper())
        return matches

    def _calculate_field_score(self, course, query_tokens, field_content, weight):
        """Calculate score for a specific field (title, description, etc.)"""
        field_tokens = self.tokenizer(field_content.lower())
        field_token_set = set(field_tokens)
        
        score = 0
        for token in query_tokens:
            if token in field_token_set:
                # Count occurrences
                count = field_tokens.count(token)
                # Boost score based on frequency and position
                score += count * weight
                
                # Additional boost for exact matches
                if token in field_content.lower():
                    score += weight * 0.5
        
        return score

    def search(self, query, eligible_course_codes=None, top_n=10):
        # Tokenize and expand query
        original_tokens = self.tokenizer(query)
        expanded_tokens = self._expand_query(original_tokens)
        
        # Get token IDs for expanded query
        token_ids = [str(self.lexicon[token]) for token in expanded_tokens if token in self.lexicon]
        
        scores = defaultdict(float)
        
        # BM25 scoring for expanded query
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
                bm25_score = idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_doc_length))
                scores[course_code] += bm25_score
        
        # Field-specific scoring
        course_map = {c['code']: c for c in self.courses}
        
        for course_code in scores.keys():
            course = course_map.get(course_code, {'code': course_code, 'title': '', 'description': ''})
            
            # Title scoring
            title_score = self._calculate_field_score(
                course, original_tokens, course['title'], self.title_weight
            )
            
            # Description scoring
            description_score = self._calculate_field_score(
                course, original_tokens, course['description'], self.description_weight
            )
            
            # Add field scores to BM25 score (no code_score)
            scores[course_code] += title_score + description_score
            
            # Boost for courses that match multiple query terms
            matching_terms = sum(1 for token in original_tokens if token in self.tokenizer(course['title'] + ' ' + course['description']))
            if matching_terms > 1:
                scores[course_code] *= (1 + matching_terms * 0.2)
        
        # Sort and get top N
        top_courses = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # Map course_code to metadata
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