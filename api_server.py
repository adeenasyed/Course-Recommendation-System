from flask import Flask, request, jsonify
from flask_cors import CORS
from CourseSearchEngine.CourseSearcher import CourseSearcher
from RequirementsAnalysis.RequirementsTreeTraveller import RequirementsTreeTraveller

app = Flask(__name__)

# Configure CORS properly
CORS(app, 
     origins=["http://localhost:8080", "http://localhost:3000", "http://localhost:5173", "http://localhost:4173"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"],
     supports_credentials=True)

# Initialize the searcher and traveller
searcher = CourseSearcher()
traveller = RequirementsTreeTraveller()

@app.route('/get-eligible-courses', methods=['POST', 'OPTIONS'])
def get_eligible_courses():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        program = data.get('program', '')
        term = data.get('term', '')
        minor = data.get('minor', None)
        
        if not program or not term:
            return jsonify({'error': 'Missing program or term'}), 400
            
        courses_with_metadata = traveller.get_available_courses(program=program, term=term, minor=minor)
        
        response = jsonify({'courses': courses_with_metadata, 'count': len(courses_with_metadata)})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        return response
        
    except Exception as e:
        response = jsonify({'error': str(e)}), 500
        if isinstance(response, tuple):
            response_obj, status_code = response
            response_obj.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
            return response_obj, status_code
        return response

@app.route('/search-courses', methods=['POST', 'OPTIONS'])
def search_courses():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        query = data.get('query', '')
        eligible_course_codes = data.get('eligible_course_codes', [])
        
        if not query:
            return jsonify({'error': 'Missing query parameter'}), 400
            
        # Use the search engine with eligible course codes filter
        results = searcher.search(query, eligible_course_codes=eligible_course_codes, top_n=20)
        
        response = jsonify({'results': results, 'count': len(results)})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        return response
        
    except Exception as e:
        response = jsonify({'error': str(e)}), 500
        if isinstance(response, tuple):
            response_obj, status_code = response
            response_obj.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
            return response_obj, status_code
        return response

@app.route('/search', methods=['GET', 'OPTIONS'])
def search():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Missing query parameter'}), 400
            
        # Call your search function (adjust as needed)
        results = searcher.search(query)
        
        response = jsonify(results)
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        return response
        
    except Exception as e:
        response = jsonify({'error': str(e)}), 500
        if isinstance(response, tuple):
            response_obj, status_code = response
            response_obj.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
            return response_obj, status_code
        return response

# Add a health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'API server is running'})

if __name__ == '__main__':
    app.run(port=5001, debug=True, host='0.0.0.0') 