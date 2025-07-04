"""
You are a course requirement parser. Extract requirements and represent them as logical groups.

PARSING RULES:
1. "PROGRAM" reqs:
   - If ALLOWED programs exist, only those programs are allowed (ignore NOT_ALLOWED programs)
   - If no ALLOWED programs exist, then use NOT_ALLOWED programs
   - Operators: "=" (ALLOWED) or "!=" (NOT_ALLOWED)

2. "FACULTY" reqs:
   - Same logic as programs, ALLOWED takes priority over NOT_ALLOWED
   - Operators: "=" (ALLOWED) or "!=" (NOT_ALLOWED)

3. "LEVEL" reqs:
   - Operators: "=" (exact level) or ">=" (minimum level)

4. "MINOR" reqs:
   - Always use "=" operator
   - Multiple minors are always OR conditions (any one qualifies)
   - Look for terms "minor" and "option"

5. Handling for the term "major":
   - Treat it as a PROGRAM

8. Handling for the term "honours":
   - Ignore "Honours" prefixes in program names

8. Ignore any information (e.g., course reqs, milestone reqs) that is not related to the above categories

9. Structure:
   - Simple requirements: single "AND" group
   - Multiple options: OR group with AND sub-groups

INPUT: "{requirements_description}"

OUTPUT FORMAT:
{
  "requirements": [
    {
      "operator": "AND" | "OR",
      "conditions": [
        {
          "type": "PROGRAM" | "FACULTY" | "LEVEL" | "MINOR",
          "operator": "=" | "!=" | ">=",
          "value": "specific value"
        }
      ]
    }
  ] or null
}

EXAMPLES:

Input: "Prereq: MATH 116; Level at least 2B Civil Engineering. Antireq: MSE 261, SYDE 262"
Output: {
  "requirements": {
      "operator": "AND",
      "conditions": [
        {"type": "LEVEL", "operator": ">=", "value": "2B"},
        {"type": "PROGRAM", "operator": "=", "value": "Civil Engineering"}
      ]
  }
}

Input: "Not open to Arts and Business students. Antireq: AFM 132, BUS 111W"
Output: {
  "requirements": {
    "operator": "AND",
    "conditions": [
      {"type": "PROGRAM", "operator": "!=", "value": "Arts and Business"}
    ]
  }
}

Input: "Prereq: Level at least 2B Architecture students or Honours Environment and Business students"
Output: {
  "requirements": {
    "operator": "OR",
    "conditions": [
      {
          "operator": "AND",
          "conditions": [
            {"type": "LEVEL", "operator": "=", "value": "2B"},
            {"type": "PROGRAM", "operator": "=", "value": "Architecture"}
          ]
      },
      {"type": "PROGRAM", "operator": "=", "value": "Environment and Business"}
    ]
  }

Input: "Prereq: MUSIC 100 or 110; 227, 270; Music majors and minors. Coreq: One of MUSIC 116, 117, 216, 217, 316, 317, 416, 417"
Output: {
"requirements": {
    "operator": "OR",
    "conditions": [
      {"type": "PROGRAM", "operator": "=", "value": "Music"},
      {"type": "MINOR", "operator": "=", "value": "Music"}
    ]
  }

Input: "Prereq: MUSIC 217; audition required"
Output: {
    null
}

}

Parse the following requirement description:

"""