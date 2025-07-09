import sys
from RequirementsAnalysis.RequirementsTreeTraveller import RequirementsTreeTraveller

def main():
    print("Course Recommendation System")
    print("---------------------------")
    program = input("Enter your program name: ").strip()
    term = input("Enter your term: ").strip().upper()
    minor = input("Enter your minor (optional, press Enter to skip): ").strip()
    if not minor:
        minor = None

    traveller = RequirementsTreeTraveller()
    courses = traveller.get_available_courses(program=program, term=term, minor=minor)

    if courses:
        print(f"\nYou can take the following courses ({len(courses)} found):")
        for c in courses:
            print(f"- {c}")
    else:
        print("\nNo available courses found for your profile.")

if __name__ == "__main__":
    main()
