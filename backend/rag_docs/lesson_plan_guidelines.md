# Lesson Plan Guidelines for Detailed Planning

## Lesson Plan Structure Requirements

### JSON Output Format
```json
{
    "lesson_plans": [
        {
            "lesson_id": 1,
            "title": "Descriptive Lesson Title",
            "learning_objectives": [
                "Specific, measurable objective 1",
                "Specific, measurable objective 2"
            ],
            "structure": {
                "introduction": "5 minutes",
                "main_content": "25 minutes", 
                "examples": "15 minutes",
                "exercises": "15 minutes",
                "summary": "5 minutes"
            },
            "activities": [
                "Interactive demonstration of concept",
                "Guided practice exercise",
                "Independent coding challenge"
            ],
            "assessment": "Description of how learning will be assessed",
            "materials_needed": [
                "Code editor",
                "Specific tools or libraries"
            ],
            "key_concepts": [
                "concept1",
                "concept2"
            ]
        }
    ],
    "generated_at": "ISO_timestamp",
    "generation_stage": "lesson_plans_complete"
}
```

## Time Allocation Guidelines

### Standard 60-Minute Lesson Structure
- **Introduction (5-8 minutes)**
  - Lesson overview and objectives
  - Connection to previous learning
  - Motivation and real-world relevance

- **Main Content (25-30 minutes)**
  - Core concept explanation
  - Theoretical foundation
  - Key principles and rules

- **Examples (10-15 minutes)**
  - Practical demonstrations
  - Code walkthroughs
  - Common use cases

- **Exercises (15-20 minutes)**
  - Hands-on practice
  - Guided and independent work
  - Problem-solving activities

- **Summary (5 minutes)**
  - Key takeaways recap
  - Next lesson preview
  - Additional resources

### Flexible Time Adjustments
- **Complex Topics**: Extend main content, reduce exercises
- **Practical Skills**: Extend exercises, reduce theory
- **Review Lessons**: More examples and practice, less new content

## Learning Objectives Framework

### Objective Categories
1. **Knowledge**: Understanding concepts and facts
2. **Comprehension**: Explaining and interpreting information
3. **Application**: Using knowledge in new situations
4. **Analysis**: Breaking down complex problems
5. **Synthesis**: Creating new solutions
6. **Evaluation**: Making judgments about quality

### Objective Verbs by Level
- **Beginner**: Define, identify, list, describe, explain
- **Intermediate**: Apply, demonstrate, implement, solve, compare
- **Advanced**: Analyze, evaluate, create, design, optimize

### Example Learning Objectives

#### Python - Variables and Data Types
- "Define the four basic data types in Python (string, integer, float, boolean)"
- "Create variables using appropriate naming conventions"
- "Convert between different data types using built-in functions"

#### JavaScript - Functions
- "Write function declarations and function expressions"
- "Implement functions with parameters and return values"
- "Apply scope rules to predict variable accessibility"

#### React - State Management
- "Create components that manage local state using useState hook"
- "Update state in response to user interactions"
- "Explain the difference between props and state"

## Activity Design Principles

### Activity Types
1. **Demonstration**: Instructor-led code examples
2. **Guided Practice**: Step-by-step student coding
3. **Independent Practice**: Solo problem-solving
4. **Pair Programming**: Collaborative coding
5. **Code Review**: Analyzing and improving code
6. **Debugging**: Finding and fixing errors

### Activity Progression
- Start with simple, guided activities
- Gradually increase complexity and independence
- End with challenging, open-ended problems

### Interactive Elements
- **Live Coding**: Real-time code demonstration
- **Code-Along**: Students follow instructor coding
- **Think-Pair-Share**: Discuss concepts with peers
- **Quick Polls**: Check understanding with questions

## Assessment Strategies

### Formative Assessment (During Lesson)
- **Code Checks**: Quick review of student code
- **Exit Tickets**: Brief questions at lesson end
- **Thumbs Up/Down**: Quick understanding check
- **Peer Review**: Students check each other's work

### Summative Assessment (End of Lesson)
- **Coding Challenges**: Complete programming tasks
- **Code Explanation**: Describe what code does
- **Debugging Exercises**: Fix broken code
- **Mini-Projects**: Apply multiple concepts

### Assessment Criteria
- **Correctness**: Code works as intended
- **Style**: Follows best practices and conventions
- **Understanding**: Can explain reasoning
- **Problem-Solving**: Approaches challenges systematically

## Materials and Resources

### Required Materials
- **Code Editor**: VS Code, PyCharm, or similar
- **Runtime Environment**: Python interpreter, Node.js, etc.
- **Browser**: For web development topics
- **Documentation**: Official language/framework docs

### Supplementary Resources
- **Cheat Sheets**: Quick reference guides
- **Video Tutorials**: Alternative explanations
- **Practice Platforms**: Coding exercise websites
- **Community Forums**: Stack Overflow, Reddit, etc.

## Differentiation Strategies

### For Different Skill Levels
- **Beginners**: More scaffolding, simpler examples
- **Intermediate**: Balanced guidance and independence
- **Advanced**: Minimal guidance, complex challenges

### For Different Learning Styles
- **Visual**: Diagrams, flowcharts, color coding
- **Auditory**: Verbal explanations, discussions
- **Kinesthetic**: Hands-on coding, physical activities

### Support Strategies
- **Struggling Students**: Additional examples, peer support
- **Advanced Students**: Extension activities, mentoring roles
- **Different Backgrounds**: Cultural context, varied examples

## Key Concepts Definition

### Concept Categories
1. **Syntax**: Language-specific rules and structure
2. **Semantics**: Meaning and behavior of code
3. **Patterns**: Common solutions and approaches
4. **Best Practices**: Industry standards and conventions
5. **Debugging**: Problem-solving and error resolution

### Concept Presentation
- **Definition**: Clear, concise explanation
- **Examples**: Multiple use cases and contexts
- **Non-Examples**: What it's not, common misconceptions
- **Applications**: Real-world usage scenarios

## Quality Assurance Checklist

### Lesson Plan Validation
- [ ] Learning objectives are specific and measurable
- [ ] Time allocations add up to 60 minutes
- [ ] Activities support the learning objectives
- [ ] Assessment methods align with objectives
- [ ] Materials list is complete and accessible
- [ ] Key concepts are clearly defined
- [ ] Progression from simple to complex is logical
- [ ] JSON structure is valid and complete
- [ ] Content is appropriate for target skill level