PROMPT_TEMPLATE = """IMPORTANT: You must only respond with valid JSON and nothing else. No explanations, no markdown, no extra text.

You are a course requirement parser. Extract requirements and represent them as logical groups. Do not infer requirements. Only extract requirements that are explicitly stated.

PARSING RULES:
1. "PROGRAM" reqs:
   - IMPORTANT: Multiple programs are always OR conditions
   - Only use these exact program names for values: #programs_list#
   - Operators: "=" (ALLOWED) or "!=" (NOT_ALLOWED)

2. "LEVEL" reqs:
   - Only use these exact levels for values: 1A, 1B, 2A, 2B, 3A, 3B, 4A, 4B
   - Operators: "=" (exact level) or ">=" (minimum level)

3. "MINOR" reqs:
   - IMPORTANT: When minors are present, they should be treated as separate OR conditions at the top level
   - Always use "=" operator
   - Look for the term "option"

4. Return null when:
   - There is no information that we are interested in (e.g., only prerequisites/antirequisites/corequisites/grades are mentioned)

5. Structure rules:
   - For simple cases like "A or B students", use simple OR with direct conditions
   - For complex cases like "Level 2B Management Engineering or Systems Design Engineering students", use OR with AND subgroups only when needed
   - Do not create unnecessary nested structures

OUTPUT FORMAT:
{
  "course": {
      "operator": "AND" | "OR",
      "conditions": [
        {
          "type": "PROGRAM" | "LEVEL" | "MINOR",
          "operator": "=" | "!=" | ">=",
          "value": "specific value"
        }
      ]
  } or null
}

EXAMPLES:

Requirements Description: "Prereq: MATH 116; Level at least 2B Civil Engineering. Antireq: MSE 261, SYDE 262"
Output: {
  "CIVE 392": {
    "operator": "AND",
    "conditions": [
      {"type": "LEVEL", "operator": ">=", "value": "2B"},
      {"type": "PROGRAM", "operator": "=", "value": "Civil Engineering"}
    ]
  }
}

Requirements Description: "Prereq: One of BIOL 273, BME 284, SYDE 384/584; Level at least 3A Biomedical Engineering or Level at least 3B Systems Design Engineering or Level at least 3B Honours Life Sciences (Biophysics Specialization). Antireq: SYDE 544"
Output: {
  "BME 544": {
    "operator": "OR",
    "conditions": [
      {
        "operator": "AND",
        "conditions": [
          {"type": "LEVEL", "operator": ">=", "value": "3A"},
          {"type": "PROGRAM", "operator": "=", "value": "Biomedical Engineering"}
        ]
      },
      {
        "operator": "AND",
        "conditions": [
          {"type": "LEVEL", "operator": ">=", "value": "3B"},
          {"type": "PROGRAM", "operator": "=", "value": "Systems Design Engineering"}
        ]
      }
    ]
  }
}

Requirements Description: "Prereq: GENE 123; Level at least 2A Mechanical Engineering or Mechatronics Option"
Output: {
  "ME 269": {
    "operator": "OR",
    "conditions": [
      {
        "operator": "AND",
        "conditions": [
          {"type": "LEVEL", "operator": ">=", "value": "2A"},
          {"type": "PROGRAM", "operator": "=", "value": "Mechanical Engineering"}
        ]
      },
      {"type": "MINOR", "operator": "=", "value": "Mechatronics"}
    ]
  }
}

Requirements Description: "Prereq: (ME 360; Mechanical Eng/Mechatronics Option) or (SYDE 352; Systems Design Eng/Mechatronics Option). Antireq: ECE 481, MTE 484"
Output: {
  "ECE 484": {
    "operator": "OR",
    "conditions": [
      {"type": "PROGRAM", "operator": "=", "value": "Mechanical Engineering"},
      {"type": "MINOR", "operator": "=", "value": "Mechatronics"},
      {"type": "PROGRAM", "operator": "=", "value": "Systems Design Engineering"}
    ]
  }
}

Parse the following requirements description for #course#. RESPOND WITH ONLY A JSON OBJECT:
#requirements_description#"""