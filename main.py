import sys
from RequirementsAnalysis.RequirementsTreeTraveller import RequirementsTreeTraveller
from CourseSearchEngine.CourseSearcher import CourseSearcher

def main():
    print("=" * 100)
    print("         Welcome to Waterloo's Undergraduate Engineering Course Recommendation System!")
    print("=" * 100)
    print()
    print("Let's help you find the best courses for Fall 2025!")
    print()
    program = input("👉 What program are you in? ").strip()
    term = input("👉 What term are you in? ").strip().upper()
    # Ask about minor/option with yes/no
    has_minor = input("👉 Are you taking an Option (enter Y/N)? ").strip().upper()
    if has_minor == "Y":
        minor = input("👉 What Option are you taking? ").strip()
    else:
        minor = None

    print("\nFinding courses you are eligible to take...")
    traveller = RequirementsTreeTraveller()
    courses = traveller.get_available_courses(program=program, term=term, minor=minor)

    if courses:
        print(f"\n📚 You are eligible to take {len(courses)} courses in Fall 2025.")
        while True:
            print("Would you like to...")
            print("  1) See the full list of eligible courses")
            print("  2) Filter the list by entering a search query")
            choice = input("Enter 1 or 2: ").strip()
            if choice == "1":
                print("\nHere are all the courses you are eligible to take:")
                for c in courses:
                    print(f"   • {c}")
                print("\nIf you want to filter this list with a search query, you can run the program again and choose option 2.")
                break 
            elif choice == "2":
                print("\n🔎 Enter a search query to find the best matches for your interests!")
                query = input("Type your query (e.g., 'machine learning', 'circuits', 'design'): ").strip()
                if query:
                    print("\nSearching for the most relevant courses for you...")
                    searcher = CourseSearcher()
                    results = searcher.search(query, eligible_course_codes=courses, top_n=10)
                    if results:
                        print("\n✨ Top 10 Recommended Courses:")
                        print("-" * 100)
                        for i, course in enumerate(results, 1):
                            print(f"{i}. {course['code']}: {course['title']}")
                            print(f"   {course['description']}")
                            print(f"   [Relevance Score: {course['score']:.4f}]\n")
                        print("-" * 100)
                        print("Good luck with your course selection! 🎉")
                    else:
                        print("Sorry, no courses matched your search query. Try a different query!")
                else:
                    print("No search query entered. Exiting. Have a great day!")
                break
            else:
                print("Invalid input. Please enter 1 or 2.")
    else:
        print("\n☹️ Sorry, no available courses found for your profile. Please check your program, term, or option and try again.")

if __name__ == "__main__":
    main()
