"""
Survey generation service for creating dynamic surveys based on subjects and difficulty levels
"""

import json
import random
from typing import Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SurveyGenerationService:
    """Service for generating dynamic surveys for different programming subjects"""
    
    # Question templates organized by subject and difficulty
    QUESTION_TEMPLATES = {
        'python': {
            'beginner': [
                {
                    'question': 'What is the correct way to create a list in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        'list = []',
                        'list = {}',
                        'list = ()',
                        'list = ""'
                    ],
                    'correct_answer': 0,
                    'topic': 'data_structures'
                },
                {
                    'question': 'Which of the following is used to define a function in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        'function',
                        'def',
                        'define',
                        'func'
                    ],
                    'correct_answer': 1,
                    'topic': 'functions'
                },
                {
                    'question': 'What is the output of print(type(5))?',
                    'type': 'multiple_choice',
                    'options': [
                        '<class \'int\'>',
                        '<class \'float\'>',
                        '<class \'str\'>',
                        '<class \'number\'>'
                    ],
                    'correct_answer': 0,
                    'topic': 'data_types'
                },
                {
                    'question': 'How do you create a comment in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        '// This is a comment',
                        '/* This is a comment */',
                        '# This is a comment',
                        '<!-- This is a comment -->'
                    ],
                    'correct_answer': 2,
                    'topic': 'syntax'
                },
                {
                    'question': 'Which operator is used for string concatenation in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        '&',
                        '+',
                        '.',
                        'concat()'
                    ],
                    'correct_answer': 1,
                    'topic': 'strings'
                }
            ],
            'intermediate': [
                {
                    'question': 'What is a list comprehension in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        'A way to create lists using a concise syntax',
                        'A method to compress lists',
                        'A function to understand lists',
                        'A type of loop'
                    ],
                    'correct_answer': 0,
                    'topic': 'list_comprehensions'
                },
                {
                    'question': 'What does the \'self\' parameter represent in a Python class method?',
                    'type': 'multiple_choice',
                    'options': [
                        'The class itself',
                        'The instance of the class',
                        'A global variable',
                        'The parent class'
                    ],
                    'correct_answer': 1,
                    'topic': 'classes'
                },
                {
                    'question': 'Which of the following is used to handle exceptions in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        'try-catch',
                        'try-except',
                        'catch-throw',
                        'handle-error'
                    ],
                    'correct_answer': 1,
                    'topic': 'exception_handling'
                },
                {
                    'question': 'What is the purpose of the __init__ method in Python classes?',
                    'type': 'multiple_choice',
                    'options': [
                        'To initialize class variables',
                        'To initialize instance variables',
                        'To destroy objects',
                        'To define class methods'
                    ],
                    'correct_answer': 1,
                    'topic': 'classes'
                },
                {
                    'question': 'What is a decorator in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        'A design pattern',
                        'A function that modifies another function',
                        'A type of class',
                        'A built-in module'
                    ],
                    'correct_answer': 1,
                    'topic': 'decorators'
                }
            ],
            'advanced': [
                {
                    'question': 'What is the Global Interpreter Lock (GIL) in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        'A mechanism that prevents multiple threads from executing Python code simultaneously',
                        'A security feature for global variables',
                        'A memory management system',
                        'A debugging tool'
                    ],
                    'correct_answer': 0,
                    'topic': 'concurrency'
                },
                {
                    'question': 'What is the difference between __str__ and __repr__ methods?',
                    'type': 'multiple_choice',
                    'options': [
                        '__str__ is for developers, __repr__ is for users',
                        '__str__ is for users, __repr__ is for developers',
                        'They are identical',
                        '__str__ is deprecated'
                    ],
                    'correct_answer': 1,
                    'topic': 'magic_methods'
                },
                {
                    'question': 'What is a metaclass in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        'A class that inherits from multiple classes',
                        'A class whose instances are classes',
                        'A class with meta information',
                        'An abstract class'
                    ],
                    'correct_answer': 1,
                    'topic': 'metaclasses'
                },
                {
                    'question': 'What is the purpose of the yield keyword in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        'To return a value from a function',
                        'To create a generator function',
                        'To pause execution',
                        'To handle exceptions'
                    ],
                    'correct_answer': 1,
                    'topic': 'generators'
                },
                {
                    'question': 'What is monkey patching in Python?',
                    'type': 'multiple_choice',
                    'options': [
                        'A debugging technique',
                        'Dynamic modification of classes or modules at runtime',
                        'A testing framework',
                        'A performance optimization'
                    ],
                    'correct_answer': 1,
                    'topic': 'dynamic_programming'
                }
            ]
        },
        'javascript': {
            'beginner': [
                {
                    'question': 'How do you declare a variable in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        'var myVar;',
                        'variable myVar;',
                        'v myVar;',
                        'declare myVar;'
                    ],
                    'correct_answer': 0,
                    'topic': 'variables'
                },
                {
                    'question': 'Which of the following is NOT a JavaScript data type?',
                    'type': 'multiple_choice',
                    'options': [
                        'string',
                        'boolean',
                        'integer',
                        'undefined'
                    ],
                    'correct_answer': 2,
                    'topic': 'data_types'
                },
                {
                    'question': 'How do you create a function in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        'function myFunction() {}',
                        'create myFunction() {}',
                        'def myFunction() {}',
                        'func myFunction() {}'
                    ],
                    'correct_answer': 0,
                    'topic': 'functions'
                },
                {
                    'question': 'What is the correct way to write a JavaScript array?',
                    'type': 'multiple_choice',
                    'options': [
                        'var colors = "red", "green", "blue"',
                        'var colors = (1:"red", 2:"green", 3:"blue")',
                        'var colors = ["red", "green", "blue"]',
                        'var colors = 1 = ("red"), 2 = ("green"), 3 = ("blue")'
                    ],
                    'correct_answer': 2,
                    'topic': 'arrays'
                },
                {
                    'question': 'How do you write "Hello World" in an alert box?',
                    'type': 'multiple_choice',
                    'options': [
                        'alertBox("Hello World");',
                        'msg("Hello World");',
                        'alert("Hello World");',
                        'msgBox("Hello World");'
                    ],
                    'correct_answer': 2,
                    'topic': 'dom'
                }
            ],
            'intermediate': [
                {
                    'question': 'What is closure in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        'A way to close the browser',
                        'A function that has access to variables in its outer scope',
                        'A method to end a loop',
                        'A type of error'
                    ],
                    'correct_answer': 1,
                    'topic': 'closures'
                },
                {
                    'question': 'What is the difference between == and === in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        '== checks type and value, === checks only value',
                        '=== checks type and value, == checks only value',
                        'They are identical',
                        '== is deprecated'
                    ],
                    'correct_answer': 1,
                    'topic': 'operators'
                },
                {
                    'question': 'What is event bubbling in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        'Events moving from child to parent elements',
                        'Events moving from parent to child elements',
                        'Creating multiple events',
                        'Preventing events'
                    ],
                    'correct_answer': 0,
                    'topic': 'events'
                },
                {
                    'question': 'What is the purpose of the \'this\' keyword in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        'Refers to the current object',
                        'Refers to the global object',
                        'Refers to the parent object',
                        'Creates a new object'
                    ],
                    'correct_answer': 0,
                    'topic': 'context'
                },
                {
                    'question': 'What is a Promise in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        'A guarantee that code will work',
                        'An object representing eventual completion of an async operation',
                        'A type of function',
                        'A debugging tool'
                    ],
                    'correct_answer': 1,
                    'topic': 'promises'
                }
            ],
            'advanced': [
                {
                    'question': 'What is the event loop in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        'A mechanism for handling asynchronous operations',
                        'A type of loop statement',
                        'A debugging feature',
                        'A performance optimization'
                    ],
                    'correct_answer': 0,
                    'topic': 'event_loop'
                },
                {
                    'question': 'What is prototypal inheritance in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        'Inheritance through classes',
                        'Inheritance through prototypes',
                        'Multiple inheritance',
                        'Interface inheritance'
                    ],
                    'correct_answer': 1,
                    'topic': 'prototypes'
                },
                {
                    'question': 'What is a WeakMap in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        'A Map with weak references to keys',
                        'A Map with limited functionality',
                        'A deprecated Map type',
                        'A Map for small datasets'
                    ],
                    'correct_answer': 0,
                    'topic': 'collections'
                },
                {
                    'question': 'What is the difference between call, apply, and bind?',
                    'type': 'multiple_choice',
                    'options': [
                        'They are identical methods',
                        'call and apply invoke immediately, bind returns a new function',
                        'Only call works with functions',
                        'bind is deprecated'
                    ],
                    'correct_answer': 1,
                    'topic': 'function_methods'
                },
                {
                    'question': 'What is a Proxy in JavaScript?',
                    'type': 'multiple_choice',
                    'options': [
                        'A network proxy',
                        'An object that intercepts operations on another object',
                        'A type of function',
                        'A debugging tool'
                    ],
                    'correct_answer': 1,
                    'topic': 'proxies'
                }
            ]
        }
    }
    
    # Subject-specific configuration
    SUBJECT_CONFIG = {
        'python': {
            'name': 'Python Programming',
            'question_count': 8,
            'difficulty_distribution': {
                'beginner': 0.4,
                'intermediate': 0.4,
                'advanced': 0.2
            },
            'topics': ['data_structures', 'functions', 'classes', 'exception_handling', 'decorators']
        },
        'javascript': {
            'name': 'JavaScript Programming',
            'question_count': 8,
            'difficulty_distribution': {
                'beginner': 0.4,
                'intermediate': 0.4,
                'advanced': 0.2
            },
            'topics': ['variables', 'functions', 'objects', 'promises', 'closures']
        }
    }
    
    @classmethod
    def generate_survey(cls, subject: str, user_id: str) -> Dict[str, Any]:
        """
        Generate a dynamic survey for a specific subject and user
        
        Args:
            subject: The programming subject (e.g., 'python', 'javascript')
            user_id: The user ID for whom the survey is being generated
            
        Returns:
            Dictionary containing the generated survey
            
        Raises:
            ValueError: If subject is not supported
        """
        if subject not in cls.QUESTION_TEMPLATES:
            raise ValueError(f"Subject '{subject}' is not supported")
        
        logger.info(f"Generating survey for subject: {subject}, user: {user_id}")
        
        subject_config = cls.SUBJECT_CONFIG[subject]
        question_count = subject_config['question_count']
        difficulty_dist = subject_config['difficulty_distribution']
        
        # Calculate number of questions per difficulty level
        questions_per_difficulty = {
            'beginner': int(question_count * difficulty_dist['beginner']),
            'intermediate': int(question_count * difficulty_dist['intermediate']),
            'advanced': int(question_count * difficulty_dist['advanced'])
        }
        
        # Ensure we have the exact number of questions
        total_assigned = sum(questions_per_difficulty.values())
        if total_assigned < question_count:
            questions_per_difficulty['intermediate'] += question_count - total_assigned
        
        # Select questions from each difficulty level
        selected_questions = []
        question_id = 1
        
        for difficulty, count in questions_per_difficulty.items():
            available_questions = cls.QUESTION_TEMPLATES[subject][difficulty].copy()
            
            if count > len(available_questions):
                # If we need more questions than available, use all and repeat some
                selected = available_questions * (count // len(available_questions) + 1)
                selected = selected[:count]
            else:
                selected = random.sample(available_questions, count)
            
            for question_template in selected:
                question = question_template.copy()
                question['id'] = question_id
                question['difficulty'] = difficulty
                selected_questions.append(question)
                question_id += 1
        
        # Shuffle questions to mix difficulties
        random.shuffle(selected_questions)
        
        survey = {
            'subject': subject,
            'subject_name': subject_config['name'],
            'user_id': user_id,
            'questions': selected_questions,
            'total_questions': len(selected_questions),
            'generated_at': datetime.utcnow().isoformat(),
            'metadata': {
                'difficulty_distribution': questions_per_difficulty,
                'topics_covered': list(set(q['topic'] for q in selected_questions))
            }
        }
        
        logger.info(f"Generated survey with {len(selected_questions)} questions for {subject}")
        return survey
    
    @classmethod
    def get_supported_subjects(cls) -> List[str]:
        """Get list of supported subjects"""
        return list(cls.QUESTION_TEMPLATES.keys())
    
    @classmethod
    def get_subject_info(cls, subject: str) -> Dict[str, Any]:
        """Get information about a specific subject"""
        if subject not in cls.SUBJECT_CONFIG:
            raise ValueError(f"Subject '{subject}' is not supported")
        
        return cls.SUBJECT_CONFIG[subject].copy()
    
    @classmethod
    def validate_survey_structure(cls, survey: Dict[str, Any]) -> bool:
        """
        Validate that a survey has the correct structure
        
        Args:
            survey: Survey dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['subject', 'user_id', 'questions', 'generated_at']
        
        # Check required top-level fields
        for field in required_fields:
            if field not in survey:
                logger.error(f"Survey missing required field: {field}")
                return False
        
        # Check questions structure
        if not isinstance(survey['questions'], list):
            logger.error("Survey questions must be a list")
            return False
        
        for question in survey['questions']:
            required_q_fields = ['id', 'question', 'type', 'options', 'correct_answer', 'difficulty', 'topic']
            for field in required_q_fields:
                if field not in question:
                    logger.error(f"Question missing required field: {field}")
                    return False
        
        return True