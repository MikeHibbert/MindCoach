"""
End-to-end tests for complete LangChain workflow
"""
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from app.services.langchain_pipeline import LangChainPipelineService
from app.services.langchain_chains import (
    SurveyGenerationChain,
    CurriculumGeneratorChain,
    LessonPlannerChain,
    ContentGeneratorChain
)

class TestLangChainEndToEndWorkflow:
    """End-to-end tests for complete LangChain workflow"""
    
    @pytest.fixture
    def complete_survey_data(self):
        """Complete survey data for end-to-end testing"""
        return {
            'user_id': 'e2e-test-user',
            'subject': 'python',
            'skill_level': 'intermediate',
            'answers': [
                {'question_id': 1, 'topic': 'variables', 'correct': True, 'difficulty': 'beginner'},
                {'question_id': 2, 'topic': 'functions', 'correct': True, 'difficulty': 'intermediate'},
                {'question_id': 3, 'topic': 'classes', 'correct': False, 'difficulty': 'intermediate'},
                {'question_id': 4, 'topic': 'decorators', 'correct': False, 'difficulty': 'advanced'},
                {'question_id': 5, 'topic': 'generators', 'correct': True, 'difficulty': 'intermediate'},
                {'question_id': 6, 'topic': 'context_managers', 'correct': False, 'difficulty': 'advanced'},
                {'question_id': 7, 'topic': 'metaclasses', 'correct': False, 'difficulty': 'advanced'}
            ],
            'submitted_at': '2024-01-15T10:00:00Z'
        }
    
    @pytest.fixture
    def expected_pipeline_results(self):
        """Expected results from complete pipeline execution"""
        return {
            'curriculum': {
                "curriculum": {
                    "subject": "python",
                    "skill_level": "intermediate",
                    "total_lessons": 10,
                    "learning_objectives": [
                        "Master intermediate Python concepts",
                        "Build practical applications",
                        "Understand advanced programming patterns"
                    ],
                    "topics": [
                        {
                            "lesson_id": i,
                            "title": f"Lesson {i}: Advanced Topic",
                            "topics": [f"topic_{i}_1", f"topic_{i}_2"],
                            "prerequisites": [f"topic_{i-1}_1"] if i > 1 else [],
                            "difficulty": "intermediate",
                            "estimated_duration": "60 minutes"
                        }
                        for i in range(1, 11)
                    ]
                },
                "generated_at": "2024-01-15T11:00:00Z",
                "generation_stage": "curriculum_complete"
            },
            'lesson_plans': {
                "lesson_plans": [
                    {
                        "lesson_id": i,
                        "title": f"Lesson {i}: Advanced Topic",
                        "learning_objectives": [
                            f"Understand concept {i}.1",
                            f"Apply technique {i}.2",
                            f"Implement solution {i}.3"
                        ],
                        "structure": {
                            "introduction": "5 minutes",
                            "main_content": "25 minutes",
                            "examples": "15 minutes",
                            "exercises": "15 minutes",
                            "summary": "5 minutes"
                        },
                        "activities": [
                            f"Activity {i}.1: Interactive demonstration",
                            f"Activity {i}.2: Guided practice",
                            f"Activity {i}.3: Independent work"
                        ],
                        "assessment": f"Assessment for lesson {i}",
                        "materials_needed": [
                            "Python IDE",
                            f"Materials for lesson {i}",
                            "Reference documentation"
                        ],
                        "key_concepts": [
                            f"concept_{i}_1",
                            f"concept_{i}_2",
                            f"concept_{i}_3"
                        ]
                    }
                    for i in range(1, 11)
                ],
                "generated_at": "2024-01-15T11:05:00Z",
                "generation_stage": "lesson_plans_complete"
            },
            'lesson_contents': [
                {
                    'lesson_id': i,
                    'content': f"""# Lesson {i}: Advanced Topic

## Introduction
Welcome to lesson {i} on advanced Python concepts...

## Learning Objectives
- Understand concept {i}.1
- Apply technique {i}.2
- Implement solution {i}.3

## Core Concepts

### Concept {i}.1
This concept covers...

### Concept {i}.2
This technique involves...

## Code Examples

### Example 1: Basic Implementation
```python
def example_{i}_function():
    return "Example {i} result"
```

### Example 2: Advanced Usage
```python
class Example{i}Class:
    def __init__(self):
        self.value = {i}
    
    def process(self):
        return self.value * 2
```

## Hands-on Exercises

### Exercise 1: Basic Practice
Implement a function that...

### Exercise 2: Intermediate Challenge
Create a class that...

### Exercise 3: Advanced Application
Build a system that...

## Summary
In this lesson, we covered advanced concepts...

## Next Steps
In the next lesson, we will explore...
"""
                }
                for i in range(1, 11)
            ]
        }
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_complete_survey_to_lessons_pipeline(self, mock_validate, complete_survey_data, expected_pipeline_results):
        """Test complete survey-to-lessons pipeline execution"""
        mock_validate.return_value = True
        
        # Mock all chain components
        mock_survey_chain = Mock()
        mock_curriculum_chain = Mock()
        mock_planner_chain = Mock()
        mock_content_chain = Mock()
        
        # Configure mock responses
        mock_curriculum_chain.generate_curriculum.return_value = expected_pipeline_results['curriculum']
        mock_planner_chain.generate_lesson_plans.return_value = expected_pipeline_results['lesson_plans']
        
        # Mock content generation for each lesson
        def mock_content_generation(lesson_plan, subject, rag_docs=None):
            lesson_id = lesson_plan.get('lesson_id', 1)
            return expected_pipeline_results['lesson_contents'][lesson_id - 1]['content']
        
        mock_content_chain.generate_content.side_effect = mock_content_generation
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain', return_value=mock_survey_chain), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
             patch('app.services.langchain_pipeline.LessonPlannerChain', return_value=mock_planner_chain), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain', return_value=mock_content_chain):
            
            pipeline = LangChainPipelineService()
            
            # Execute complete pipeline
            start_time = time.time()
            result = pipeline.run_full_pipeline(complete_survey_data, 'python')
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Verify pipeline execution
            assert result['status'] == 'completed'
            assert result['subject'] == 'python'
            assert 'curriculum' in result
            assert 'lesson_plans' in result
            assert 'lesson_contents' in result
            
            # Verify curriculum generation
            curriculum = result['curriculum']
            assert curriculum['curriculum']['subject'] == 'python'
            assert curriculum['curriculum']['skill_level'] == 'intermediate'
            assert curriculum['curriculum']['total_lessons'] == 10
            assert len(curriculum['curriculum']['topics']) == 10
            
            # Verify lesson plans generation
            lesson_plans = result['lesson_plans']
            assert len(lesson_plans['lesson_plans']) == 10
            for i, plan in enumerate(lesson_plans['lesson_plans'], 1):
                assert plan['lesson_id'] == i
                assert len(plan['learning_objectives']) == 3
                assert 'structure' in plan
                assert 'activities' in plan
                assert 'assessment' in plan
            
            # Verify lesson content generation
            lesson_contents = result['lesson_contents']
            assert len(lesson_contents) == 10
            for i, content in enumerate(lesson_contents, 1):
                assert content['lesson_id'] == i
                assert 'content' in content
                assert f"# Lesson {i}" in content['content']
                assert "## Learning Objectives" in content['content']
                assert "## Code Examples" in content['content']
                assert "## Hands-on Exercises" in content['content']
            
            # Verify method calls
            mock_curriculum_chain.generate_curriculum.assert_called_once_with(
                complete_survey_data, 'python', []
            )
            mock_planner_chain.generate_lesson_plans.assert_called_once_with(
                expected_pipeline_results['curriculum'], 'python', []
            )
            assert mock_content_chain.generate_content.call_count == 10
            
            # Performance check
            assert execution_time < 10.0  # Should complete within 10 seconds
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_content_quality_and_personalization(self, mock_validate, complete_survey_data):
        """Test content quality and personalization in pipeline"""
        mock_validate.return_value = True
        
        # Mock chains with quality-focused responses
        mock_curriculum_chain = Mock()
        mock_planner_chain = Mock()
        mock_content_chain = Mock()
        
        # Mock high-quality curriculum
        quality_curriculum = {
            "curriculum": {
                "subject": "python",
                "skill_level": "intermediate",
                "total_lessons": 10,
                "learning_objectives": [
                    "Master object-oriented programming concepts",
                    "Implement advanced data structures",
                    "Apply design patterns effectively"
                ],
                "topics": [
                    {
                        "lesson_id": 1,
                        "title": "Advanced Object-Oriented Programming",
                        "topics": ["classes", "inheritance", "polymorphism"],
                        "prerequisites": [],
                        "difficulty": "intermediate"
                    },
                    {
                        "lesson_id": 2,
                        "title": "Decorators and Context Managers",
                        "topics": ["decorators", "context_managers", "advanced_functions"],
                        "prerequisites": ["classes"],
                        "difficulty": "advanced"
                    }
                ]
            }
        }
        
        # Mock detailed lesson plans
        quality_lesson_plans = {
            "lesson_plans": [
                {
                    "lesson_id": 1,
                    "title": "Advanced Object-Oriented Programming",
                    "learning_objectives": [
                        "Understand inheritance and polymorphism",
                        "Implement abstract classes and interfaces",
                        "Apply SOLID principles"
                    ],
                    "structure": {
                        "introduction": "10 minutes",
                        "main_content": "30 minutes",
                        "examples": "15 minutes",
                        "exercises": "15 minutes"
                    },
                    "activities": [
                        "Interactive class hierarchy design",
                        "Polymorphism implementation exercise",
                        "SOLID principles code review"
                    ],
                    "assessment": "Build a complete OOP system",
                    "key_concepts": ["inheritance", "polymorphism", "abstraction"]
                },
                {
                    "lesson_id": 2,
                    "title": "Decorators and Context Managers",
                    "learning_objectives": [
                        "Create custom decorators",
                        "Implement context managers",
                        "Understand advanced function concepts"
                    ],
                    "structure": {
                        "introduction": "10 minutes",
                        "main_content": "30 minutes",
                        "examples": "15 minutes",
                        "exercises": "15 minutes"
                    },
                    "activities": [
                        "Decorator creation workshop",
                        "Context manager implementation",
                        "Advanced function patterns"
                    ],
                    "assessment": "Build decorator and context manager library",
                    "key_concepts": ["decorators", "context_managers", "closures"]
                }
            ]
        }
        
        # Mock comprehensive content
        def mock_quality_content(lesson_plan, subject, rag_docs=None):
            lesson_id = lesson_plan.get('lesson_id', 1)
            title = lesson_plan.get('title', 'Lesson')
            objectives = lesson_plan.get('learning_objectives', [])
            concepts = lesson_plan.get('key_concepts', [])
            
            return f"""# {title}

## Introduction
This comprehensive lesson covers {', '.join(concepts)} in Python programming.

## Learning Objectives
{chr(10).join(f'- {obj}' for obj in objectives)}

## Core Concepts
{chr(10).join(f'### {concept.replace("_", " ").title()}{chr(10)}Detailed explanation of {concept}...' for concept in concepts)}

## Code Examples

### Example 1: Basic Implementation
```python
# Practical example demonstrating {concepts[0] if concepts else 'concept'}
class Example:
    def __init__(self):
        self.value = "example"
    
    def demonstrate(self):
        return f"Demonstrating {concepts[0] if concepts else 'concept'}"
```

### Example 2: Advanced Usage
```python
# Advanced implementation showing best practices
def advanced_example():
    '''
    This function demonstrates advanced usage of {concepts[0] if concepts else 'concept'}
    '''
    return "Advanced implementation"
```

## Hands-on Exercises

### Exercise 1: Basic Implementation
Create a basic implementation that demonstrates understanding of {concepts[0] if concepts else 'the concept'}.

### Exercise 2: Intermediate Challenge
Build a more complex system that combines multiple concepts.

### Exercise 3: Advanced Application
Design and implement a real-world application using all learned concepts.

### Exercise 4: Code Review
Review and improve existing code using best practices.

### Exercise 5: Performance Optimization
Optimize the implementation for better performance.

## Assessment Criteria
- Code quality and organization
- Proper use of {', '.join(concepts)}
- Implementation of best practices
- Problem-solving approach

## Summary
This lesson provided comprehensive coverage of {', '.join(concepts)}, including practical examples and hands-on exercises.

## Next Steps
In the next lesson, we will build upon these concepts to explore more advanced topics.
"""
        
        mock_curriculum_chain.generate_curriculum.return_value = quality_curriculum
        mock_planner_chain.generate_lesson_plans.return_value = quality_lesson_plans
        mock_content_chain.generate_content.side_effect = mock_quality_content
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
             patch('app.services.langchain_pipeline.LessonPlannerChain', return_value=mock_planner_chain), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain', return_value=mock_content_chain):
            
            pipeline = LangChainPipelineService()
            result = pipeline.run_full_pipeline(complete_survey_data, 'python')
            
            # Verify content quality
            curriculum = result['curriculum']['curriculum']
            
            # Check personalization based on survey data
            # User was weak in classes, decorators, context_managers, metaclasses
            # So curriculum should focus on these areas
            topic_titles = [topic['title'] for topic in curriculum['topics']]
            assert any('Object-Oriented' in title for title in topic_titles)
            assert any('Decorators' in title for title in topic_titles)
            
            # Verify lesson content quality
            lesson_contents = result['lesson_contents']
            for content_item in lesson_contents[:2]:  # Check first 2 lessons
                content = content_item['content']
                
                # Quality checks
                assert len(content) > 1000  # Substantial content
                assert content.count('##') >= 5  # Multiple sections
                assert content.count('```python') >= 2  # At least 2 code examples
                assert content.count('### Exercise') >= 3  # At least 3 exercises
                assert '## Learning Objectives' in content
                assert '## Core Concepts' in content
                assert '## Code Examples' in content
                assert '## Hands-on Exercises' in content
                assert '## Summary' in content
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_error_handling_and_recovery(self, mock_validate, complete_survey_data):
        """Test pipeline error handling and recovery mechanisms"""
        mock_validate.return_value = True
        
        # Test different error scenarios
        error_scenarios = [
            ('curriculum_generation', Exception("Curriculum generation failed")),
            ('lesson_planning', ValueError("Invalid lesson plan format")),
            ('content_generation', RuntimeError("Content generation timeout"))
        ]
        
        for error_stage, error in error_scenarios:
            mock_curriculum_chain = Mock()
            mock_planner_chain = Mock()
            mock_content_chain = Mock()
            
            # Configure error at specific stage
            if error_stage == 'curriculum_generation':
                mock_curriculum_chain.generate_curriculum.side_effect = error
            elif error_stage == 'lesson_planning':
                mock_curriculum_chain.generate_curriculum.return_value = {"curriculum": {"topics": []}}
                mock_planner_chain.generate_lesson_plans.side_effect = error
            elif error_stage == 'content_generation':
                mock_curriculum_chain.generate_curriculum.return_value = {"curriculum": {"topics": [{"lesson_id": 1}]}}
                mock_planner_chain.generate_lesson_plans.return_value = {"lesson_plans": [{"lesson_id": 1}]}
                mock_content_chain.generate_content.side_effect = error
            
            with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
                 patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
                 patch('app.services.langchain_pipeline.LessonPlannerChain', return_value=mock_planner_chain), \
                 patch('app.services.langchain_pipeline.ContentGeneratorChain', return_value=mock_content_chain):
                
                pipeline = LangChainPipelineService()
                
                # Verify error is properly propagated
                with pytest.raises(type(error), match=str(error)):
                    pipeline.run_full_pipeline(complete_survey_data, 'python')
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_performance_benchmarks(self, mock_validate, complete_survey_data):
        """Test pipeline performance benchmarks"""
        mock_validate.return_value = True
        
        # Mock chains with realistic processing delays
        mock_curriculum_chain = Mock()
        mock_planner_chain = Mock()
        mock_content_chain = Mock()
        
        def mock_curriculum_with_delay(*args, **kwargs):
            time.sleep(0.1)  # Simulate 100ms processing
            return {
                "curriculum": {
                    "subject": "python",
                    "total_lessons": 5,  # Smaller for performance test
                    "topics": [{"lesson_id": i} for i in range(1, 6)]
                }
            }
        
        def mock_lesson_plans_with_delay(*args, **kwargs):
            time.sleep(0.1)  # Simulate 100ms processing
            return {
                "lesson_plans": [{"lesson_id": i, "title": f"Lesson {i}"} for i in range(1, 6)]
            }
        
        def mock_content_with_delay(*args, **kwargs):
            time.sleep(0.05)  # Simulate 50ms processing per lesson
            return "Generated lesson content..."
        
        mock_curriculum_chain.generate_curriculum.side_effect = mock_curriculum_with_delay
        mock_planner_chain.generate_lesson_plans.side_effect = mock_lesson_plans_with_delay
        mock_content_chain.generate_content.side_effect = mock_content_with_delay
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
             patch('app.services.langchain_pipeline.LessonPlannerChain', return_value=mock_planner_chain), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain', return_value=mock_content_chain):
            
            pipeline = LangChainPipelineService()
            
            # Measure performance
            start_time = time.time()
            result = pipeline.run_full_pipeline(complete_survey_data, 'python')
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Performance benchmarks
            assert execution_time < 5.0  # Should complete within 5 seconds
            assert result['status'] == 'completed'
            assert len(result['lesson_contents']) == 5
            
            # Calculate throughput
            lessons_per_second = len(result['lesson_contents']) / execution_time
            assert lessons_per_second > 1.0  # Should generate at least 1 lesson per second
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_with_different_skill_levels(self, mock_validate):
        """Test pipeline behavior with different skill levels"""
        mock_validate.return_value = True
        
        skill_levels = ['beginner', 'intermediate', 'advanced']
        
        for skill_level in skill_levels:
            survey_data = {
                'user_id': f'test-user-{skill_level}',
                'subject': 'python',
                'skill_level': skill_level,
                'answers': [
                    {'question_id': i, 'topic': f'topic_{i}', 'correct': skill_level != 'beginner'}
                    for i in range(1, 8)
                ]
            }
            
            # Mock chains with skill-level appropriate responses
            mock_curriculum_chain = Mock()
            mock_planner_chain = Mock()
            mock_content_chain = Mock()
            
            # Curriculum should adapt to skill level
            curriculum_response = {
                "curriculum": {
                    "subject": "python",
                    "skill_level": skill_level,
                    "total_lessons": 10,
                    "topics": [
                        {
                            "lesson_id": i,
                            "title": f"{skill_level.title()} Lesson {i}",
                            "difficulty": skill_level,
                            "topics": [f"{skill_level}_topic_{i}"]
                        }
                        for i in range(1, 11)
                    ]
                }
            }
            
            lesson_plans_response = {
                "lesson_plans": [
                    {
                        "lesson_id": i,
                        "title": f"{skill_level.title()} Lesson {i}",
                        "learning_objectives": [f"{skill_level.title()} objective {i}"]
                    }
                    for i in range(1, 11)
                ]
            }
            
            def skill_appropriate_content(lesson_plan, subject, rag_docs=None):
                return f"# {skill_level.title()} Level Content\n\nThis content is appropriate for {skill_level} learners..."
            
            mock_curriculum_chain.generate_curriculum.return_value = curriculum_response
            mock_planner_chain.generate_lesson_plans.return_value = lesson_plans_response
            mock_content_chain.generate_content.side_effect = skill_appropriate_content
            
            with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
                 patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
                 patch('app.services.langchain_pipeline.LessonPlannerChain', return_value=mock_planner_chain), \
                 patch('app.services.langchain_pipeline.ContentGeneratorChain', return_value=mock_content_chain):
                
                pipeline = LangChainPipelineService()
                result = pipeline.run_full_pipeline(survey_data, 'python')
                
                # Verify skill-level appropriate content
                curriculum = result['curriculum']['curriculum']
                assert curriculum['skill_level'] == skill_level
                
                # Check that lesson titles reflect skill level
                for topic in curriculum['topics']:
                    assert skill_level.title() in topic['title']
                    assert topic['difficulty'] == skill_level
                
                # Check lesson content appropriateness
                for content_item in result['lesson_contents']:
                    content = content_item['content']
                    assert f"{skill_level.title()} Level Content" in content
                    assert f"appropriate for {skill_level} learners" in content
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_integration_with_rag_documents(self, mock_validate, complete_survey_data):
        """Test pipeline integration with RAG documents"""
        mock_validate.return_value = True
        
        # Mock RAG documents for different stages
        rag_documents = {
            'curriculum': [
                "Create comprehensive curriculum based on assessment",
                "Adapt difficulty to learner skill level",
                "Skip topics already mastered"
            ],
            'lesson_plans': [
                "Design 60-minute structured lessons",
                "Include interactive activities",
                "Provide clear assessment criteria"
            ],
            'content': [
                "Generate engaging lesson content",
                "Include 2 code examples per lesson",
                "Create 3-5 practical exercises"
            ]
        }
        
        mock_curriculum_chain = Mock()
        mock_planner_chain = Mock()
        mock_content_chain = Mock()
        
        # Mock responses that show RAG document influence
        mock_curriculum_chain.generate_curriculum.return_value = {
            "curriculum": {
                "subject": "python",
                "skill_level": "intermediate",
                "total_lessons": 10,
                "topics": [{"lesson_id": i, "title": f"Comprehensive Lesson {i}"} for i in range(1, 11)]
            }
        }
        
        mock_planner_chain.generate_lesson_plans.return_value = {
            "lesson_plans": [
                {
                    "lesson_id": i,
                    "title": f"Structured 60-minute Lesson {i}",
                    "structure": {"total_duration": "60 minutes"},
                    "activities": ["Interactive activity 1", "Interactive activity 2"],
                    "assessment": "Clear assessment criteria"
                }
                for i in range(1, 11)
            ]
        }
        
        def rag_influenced_content(lesson_plan, subject, rag_docs=None):
            lesson_id = lesson_plan.get('lesson_id', 1)
            return f"""# Engaging Lesson {lesson_id}

## Code Examples

### Example 1: Practical Implementation
```python
def example_function():
    return "First code example"
```

### Example 2: Advanced Usage
```python
class ExampleClass:
    def method(self):
        return "Second code example"
```

## Practical Exercises

### Exercise 1: Basic Practice
Complete this basic exercise...

### Exercise 2: Intermediate Challenge
Solve this intermediate problem...

### Exercise 3: Advanced Application
Build this advanced solution...

### Exercise 4: Real-world Project
Create a practical project...

### Exercise 5: Code Review
Review and improve code...
"""
        
        mock_content_chain.generate_content.side_effect = rag_influenced_content
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
             patch('app.services.langchain_pipeline.LessonPlannerChain', return_value=mock_planner_chain), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain', return_value=mock_content_chain):
            
            pipeline = LangChainPipelineService()
            result = pipeline.run_full_pipeline(complete_survey_data, 'python', rag_documents)
            
            # Verify RAG document influence
            curriculum = result['curriculum']['curriculum']
            lesson_plans = result['lesson_plans']['lesson_plans']
            lesson_contents = result['lesson_contents']
            
            # Check curriculum shows RAG influence
            for topic in curriculum['topics']:
                assert 'Comprehensive' in topic['title']
            
            # Check lesson plans show RAG influence
            for plan in lesson_plans:
                assert '60-minute' in plan['title']
                assert plan['structure']['total_duration'] == '60 minutes'
                assert len(plan['activities']) >= 2
                assert 'Interactive' in plan['activities'][0]
            
            # Check content shows RAG influence
            for content_item in lesson_contents:
                content = content_item['content']
                assert 'Engaging Lesson' in content
                assert content.count('```python') >= 2  # At least 2 code examples
                assert content.count('### Exercise') >= 3  # At least 3 exercises
            
            # Verify RAG documents were passed to chains
            mock_curriculum_chain.generate_curriculum.assert_called_once_with(
                complete_survey_data, 'python', rag_documents['curriculum']
            )
            mock_planner_chain.generate_lesson_plans.assert_called_once_with(
                result['curriculum'], 'python', rag_documents['lesson_plans']
            )
            
            # Content generation should be called for each lesson with RAG docs
            assert mock_content_chain.generate_content.call_count == 10
            for call in mock_content_chain.generate_content.call_args_list:
                args, kwargs = call
                # Third argument should be RAG docs
                if len(args) >= 3:
                    assert args[2] == rag_documents['content']