# Survey Guidelines for Knowledge Assessment

## Survey Structure Requirements

### Question Count
- **Minimum**: 5 questions per subject
- **Maximum**: 10 questions per subject
- **Recommended**: 7-8 questions for comprehensive assessment

### Difficulty Distribution
- **Beginner**: 30-40% of questions (2-3 questions)
- **Intermediate**: 40-50% of questions (3-4 questions)
- **Advanced**: 20-30% of questions (1-2 questions)

## Question Format Standards

### Multiple Choice Questions
All questions should follow this JSON structure:

```json
{
    "id": 1,
    "question": "Clear, unambiguous question text",
    "type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "difficulty": "beginner|intermediate|advanced",
    "topic": "specific_topic_name"
}
```

### Question Writing Guidelines

#### Question Text
- Use clear, concise language
- Avoid ambiguous wording
- Focus on one concept per question
- Include code snippets when testing practical knowledge

#### Answer Options
- Provide exactly 4 options (A, B, C, D)
- Make all options plausible to someone with partial knowledge
- Avoid "all of the above" or "none of the above" options
- Ensure only one option is clearly correct

#### Distractors (Incorrect Options)
- Base on common misconceptions or mistakes
- Should be clearly wrong to someone with proper understanding
- Avoid trick questions or overly subtle distinctions

## Difficulty Level Definitions

### Beginner Questions
- Test basic terminology and concepts
- Focus on recognition rather than application
- Cover fundamental syntax and simple operations

**Example Topics:**
- Variable declaration
- Basic data types
- Simple function calls
- Basic syntax rules

### Intermediate Questions
- Test understanding of concepts in context
- Require application of knowledge
- May involve reading and understanding code

**Example Topics:**
- Control flow logic
- Function parameters and return values
- Object/data structure manipulation
- Error handling basics

### Advanced Questions
- Test deep understanding and problem-solving
- May require analyzing complex code
- Focus on best practices and optimization

**Example Topics:**
- Algorithm complexity
- Design patterns
- Advanced language features
- Performance considerations

## Topic Coverage Requirements

### Core Topics (Must Include)
Each subject survey must cover these fundamental areas:

#### Programming Fundamentals
- Variables and data types
- Control structures (if/else, loops)
- Functions and scope
- Basic error handling

#### Subject-Specific Core Concepts
- **Python**: Lists, dictionaries, classes, modules
- **JavaScript**: Objects, arrays, functions, DOM basics
- **React**: Components, props, state, hooks

### Assessment Criteria

#### Skill Level Determination
Based on survey results, classify learners as:

- **Beginner (0-40% correct)**
  - Needs fundamental concepts
  - Start with basic syntax and operations
  - Focus on hands-on practice

- **Intermediate (41-70% correct)**
  - Has basic understanding
  - Ready for practical applications
  - Can handle moderate complexity

- **Advanced (71-100% correct)**
  - Strong foundational knowledge
  - Ready for complex topics
  - Can focus on best practices and optimization

## Question Examples by Subject

### Python Example Questions

#### Beginner
```json
{
    "id": 1,
    "question": "Which of the following is the correct way to create a list in Python?",
    "type": "multiple_choice",
    "options": [
        "my_list = [1, 2, 3]",
        "my_list = (1, 2, 3)",
        "my_list = {1, 2, 3}",
        "my_list = <1, 2, 3>"
    ],
    "correct_answer": "my_list = [1, 2, 3]",
    "difficulty": "beginner",
    "topic": "data_structures"
}
```

#### Intermediate
```json
{
    "id": 2,
    "question": "What will be the output of this code?\n\n```python\nfor i in range(3):\n    if i == 1:\n        continue\n    print(i)\n```",
    "type": "multiple_choice",
    "options": ["0 1 2", "0 2", "1 2", "0 1"],
    "correct_answer": "0 2",
    "difficulty": "intermediate",
    "topic": "control_flow"
}
```

#### Advanced
```json
{
    "id": 3,
    "question": "Which approach is most efficient for checking if an item exists in a large collection?",
    "type": "multiple_choice",
    "options": [
        "Using a list with 'in' operator",
        "Using a set with 'in' operator", 
        "Using a dictionary with 'in' operator on keys",
        "Both B and C are equally efficient"
    ],
    "correct_answer": "Both B and C are equally efficient",
    "difficulty": "advanced",
    "topic": "performance"
}
```

## Quality Assurance Checklist

### Before Publishing Survey
- [ ] All questions have exactly one correct answer
- [ ] Difficulty distribution matches requirements
- [ ] All code examples are tested and functional
- [ ] Question topics cover core subject areas
- [ ] Language is clear and unambiguous
- [ ] Distractors are plausible but clearly incorrect
- [ ] JSON structure is valid and complete