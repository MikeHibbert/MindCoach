# Curriculum Guidelines for Learning Path Generation

## Curriculum Structure Requirements

### Overall Structure
A complete curriculum should contain:
- **Total Lessons**: Exactly 10 lessons
- **Progression**: Logical skill building from basic to advanced
- **Coverage**: Comprehensive topic coverage for the subject
- **Personalization**: Adapted based on learner's assessed skill level

### JSON Output Format
```json
{
    "curriculum": {
        "subject": "subject_name",
        "skill_level": "beginner|intermediate|advanced",
        "total_lessons": 10,
        "learning_objectives": [
            "High-level learning goal 1",
            "High-level learning goal 2"
        ],
        "topics": [
            {
                "lesson_id": 1,
                "title": "Descriptive Lesson Title",
                "topics": ["topic1", "topic2", "topic3"],
                "prerequisites": ["previous_topic"],
                "difficulty": "beginner|intermediate|advanced",
                "estimated_duration": "45-60 minutes"
            }
        ]
    },
    "generated_at": "ISO_timestamp",
    "generation_stage": "curriculum_complete"
}
```

## Skill Level Adaptations

### Beginner Level Curriculum
- **Focus**: Fundamental concepts and basic syntax
- **Pacing**: Slower progression with more reinforcement
- **Examples**: Simple, practical applications
- **Prerequisites**: Minimal assumed knowledge

**Lesson Distribution:**
- Lessons 1-3: Core fundamentals
- Lessons 4-6: Basic applications
- Lessons 7-8: Combining concepts
- Lessons 9-10: Simple projects

### Intermediate Level Curriculum
- **Focus**: Practical applications and problem-solving
- **Pacing**: Moderate progression with real-world examples
- **Examples**: More complex scenarios and use cases
- **Prerequisites**: Basic understanding assumed

**Lesson Distribution:**
- Lessons 1-2: Review and advanced fundamentals
- Lessons 3-6: Core practical skills
- Lessons 7-9: Advanced applications
- Lesson 10: Comprehensive project

### Advanced Level Curriculum
- **Focus**: Best practices, optimization, and complex patterns
- **Pacing**: Faster progression with challenging material
- **Examples**: Industry-standard practices and patterns
- **Prerequisites**: Strong foundational knowledge

**Lesson Distribution:**
- Lesson 1: Advanced concepts overview
- Lessons 2-4: Complex patterns and techniques
- Lessons 5-7: Performance and optimization
- Lessons 8-10: Professional development practices

## Topic Progression Principles

### Logical Sequencing
- Each lesson should build on previous knowledge
- Prerequisites must be clearly defined
- Avoid circular dependencies between topics

### Skill Building
- Start with concrete concepts before abstract ones
- Introduce complexity gradually
- Provide multiple opportunities to practice new skills

### Knowledge Gaps
- Skip topics the learner already knows (based on survey)
- Replace skipped beginner topics with more advanced material
- Maintain 10-lesson structure regardless of skill level

## Subject-Specific Requirements

### Python Curriculum
**Core Topics to Cover:**
- Variables and data types
- Control structures (if/else, loops)
- Functions and scope
- Data structures (lists, dictionaries, sets)
- Object-oriented programming basics
- File handling and I/O
- Error handling and debugging
- Modules and packages
- Testing fundamentals
- Best practices and style

### JavaScript Curriculum
**Core Topics to Cover:**
- Variables and data types
- Functions and scope
- Objects and arrays
- DOM manipulation
- Event handling
- Asynchronous programming (callbacks, promises)
- ES6+ features
- Error handling
- Testing basics
- Modern development practices

### React Curriculum
**Core Topics to Cover:**
- Component fundamentals
- JSX syntax and usage
- Props and state management
- Event handling in React
- Component lifecycle
- Hooks (useState, useEffect, custom hooks)
- Conditional rendering and lists
- Forms and controlled components
- State management patterns
- Testing React components

## Learning Objectives Guidelines

### Objective Characteristics
- **Specific**: Clearly defined outcomes
- **Measurable**: Can be assessed through exercises
- **Achievable**: Realistic for the skill level
- **Relevant**: Directly applicable to real-world use
- **Time-bound**: Achievable within lesson timeframe

### Objective Examples

#### Good Learning Objectives
- "Create and manipulate Python dictionaries to store and retrieve data"
- "Implement error handling using try/except blocks"
- "Build a React component that manages its own state"

#### Poor Learning Objectives
- "Understand Python" (too vague)
- "Learn everything about functions" (too broad)
- "Become an expert" (not measurable)

## Personalization Strategies

### Based on Survey Results
- **High Performance**: Skip basic topics, add advanced concepts
- **Low Performance**: Include more foundational material
- **Mixed Performance**: Customize based on specific knowledge gaps

### Topic Substitution Rules
- If learner knows basic syntax → Replace with advanced syntax features
- If learner knows basic data structures → Add algorithm complexity
- If learner knows basic functions → Include functional programming concepts

### Difficulty Adjustment
- **Beginner**: More guided examples, step-by-step instructions
- **Intermediate**: Balanced guidance and independent work
- **Advanced**: Minimal guidance, focus on best practices

## Quality Assurance Checklist

### Curriculum Validation
- [ ] Exactly 10 lessons defined
- [ ] Logical progression from lesson 1 to 10
- [ ] All prerequisites are covered in earlier lessons
- [ ] Learning objectives are specific and measurable
- [ ] Difficulty levels are appropriate for target skill level
- [ ] Core subject topics are adequately covered
- [ ] JSON structure is valid and complete
- [ ] Estimated durations are realistic (45-60 minutes per lesson)