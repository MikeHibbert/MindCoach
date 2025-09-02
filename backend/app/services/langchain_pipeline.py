"""
LangChain pipeline orchestration service
"""
import logging
from typing import Dict, Any, List, Optional
from .langchain_chains import (
    SurveyGenerationChain,
    CurriculumGeneratorChain,
    LessonPlannerChain,
    ContentGeneratorChain
)
from .langchain_base import validate_environment, test_xai_connection

logger = logging.getLogger(__name__)

class LangChainPipelineService:
    """Service to orchestrate the three-stage LangChain content generation pipeline"""
    
    def __init__(self):
        """Initialize the pipeline service"""
        env_valid = validate_environment()
        
        if env_valid:
            # Initialize all chain components with optimized token limits to prevent timeouts
            self.survey_chain = SurveyGenerationChain(temperature=0.8, max_tokens=2500)
            self.curriculum_chain = CurriculumGeneratorChain(temperature=0.7, max_tokens=2000)
            self.lesson_planner_chain = LessonPlannerChain(temperature=0.7, max_tokens=1500)
            self.content_generator_chain = ContentGeneratorChain(temperature=0.6, max_tokens=2000)
            self.mock_mode = False
            logger.info("LangChain pipeline service initialized with API")
        else:
            # Initialize in mock mode for testing
            self.survey_chain = None
            self.curriculum_chain = None
            self.lesson_planner_chain = None
            self.content_generator_chain = None
            self.mock_mode = True
            logger.warning("LangChain pipeline service initialized in MOCK MODE (no API key)")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to xAI API"""
        logger.info("Testing xAI API connection")
        
        try:
            success, response = test_xai_connection()
            return {
                "status": "success" if success else "error",
                "message": response,
                "timestamp": "2024-01-15T10:00:00Z"  # Will be replaced with actual timestamp
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": "2024-01-15T10:00:00Z"
            }
    
    def generate_survey(self, subject: str, rag_docs: List[str] = None) -> Dict[str, Any]:
        """Generate survey questions for a subject"""
        logger.info(f"Starting survey generation for subject: {subject}")
        
        try:
            result = self.survey_chain.generate_survey(subject, rag_docs)
            logger.info(f"Survey generation completed for {subject}")
            return result
            
        except Exception as e:
            logger.error(f"Survey generation failed for {subject}: {e}")
            raise
    
    def generate_curriculum(self, survey_data: Dict[str, Any], subject: str, rag_docs: List[str] = None) -> Dict[str, Any]:
        """Stage 1: Generate curriculum scheme based on survey results"""
        logger.info(f"Starting Stage 1: Curriculum generation for {subject}")
        logger.info(f"Survey data received: user_id={survey_data.get('user_id')}, skill_level={survey_data.get('skill_level')}, accuracy={survey_data.get('accuracy')}")
        
        if self.mock_mode:
            logger.info("Using mock curriculum generation")
            return self._generate_mock_curriculum(survey_data, subject)
        
        try:
            logger.info(f"Calling curriculum chain for {subject}")
            result = self.curriculum_chain.generate_curriculum(survey_data, subject, rag_docs)
            logger.info(f"Stage 1 completed: Curriculum generated for {subject}, result keys: {list(result.keys()) if result else 'None'}")
            return result
            
        except Exception as e:
            logger.error(f"Stage 1 failed: Curriculum generation error for {subject}: {e}", exc_info=True)
            raise
    
    def generate_lesson_plans(self, curriculum_data: Dict[str, Any], subject: str, rag_docs: List[str] = None) -> Dict[str, Any]:
        """Stage 2: Generate lesson plans based on curriculum"""
        logger.info(f"Starting Stage 2: Lesson planning for {subject}")
        
        if self.mock_mode:
            logger.info("Using mock lesson plans generation")
            return self._generate_mock_lesson_plans(curriculum_data, subject)
        
        try:
            result = self.lesson_planner_chain.generate_lesson_plans(curriculum_data, subject, rag_docs)
            logger.info(f"Stage 2 completed: Lesson plans generated for {subject}")
            return result
            
        except Exception as e:
            logger.error(f"Stage 2 failed: Lesson planning error for {subject}: {e}")
            raise
    
    def generate_lesson_content(self, lesson_plan: Dict[str, Any], subject: str, rag_docs: List[str] = None) -> str:
        """Stage 3: Generate lesson content based on lesson plan"""
        lesson_id = lesson_plan.get('lesson_id', 'unknown')
        logger.info(f"Starting Stage 3: Content generation for lesson {lesson_id} in {subject}")
        
        if self.mock_mode:
            logger.info(f"Using mock content generation for lesson {lesson_id}")
            return self._generate_mock_lesson_content(lesson_plan, subject)
        
        try:
            result = self.content_generator_chain.generate_content(lesson_plan, subject, rag_docs)
            logger.info(f"Stage 3 completed: Content generated for lesson {lesson_id}")
            return result
            
        except Exception as e:
            logger.error(f"Stage 3 failed: Content generation error for lesson {lesson_id}: {e}")
            raise
    
    def run_full_pipeline(self, survey_data: Dict[str, Any], subject: str, rag_docs: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """Run the complete three-stage pipeline"""
        logger.info(f"Starting full LangChain pipeline for {subject}")
        
        if not rag_docs:
            rag_docs = {}
        
        try:
            # Stage 1: Generate curriculum
            logger.info("Pipeline Stage 1: Generating curriculum")
            curriculum_data = self.generate_curriculum(
                survey_data, 
                subject, 
                rag_docs.get('curriculum', [])
            )
            
            # Stage 2: Generate lesson plans
            logger.info("Pipeline Stage 2: Generating lesson plans")
            lesson_plans_data = self.generate_lesson_plans(
                curriculum_data, 
                subject, 
                rag_docs.get('lesson_plans', [])
            )
            
            # Stage 3: Generate content for each lesson
            logger.info("Pipeline Stage 3: Generating lesson content")
            lesson_contents = []
            
            for lesson_plan in lesson_plans_data.get('lesson_plans', []):
                content = self.generate_lesson_content(
                    lesson_plan, 
                    subject, 
                    rag_docs.get('content', [])
                )
                lesson_contents.append({
                    'lesson_id': lesson_plan.get('lesson_id'),
                    'content': content
                })
            
            result = {
                'status': 'completed',
                'curriculum': curriculum_data,
                'lesson_plans': lesson_plans_data,
                'lesson_contents': lesson_contents,
                'subject': subject
            }
            
            logger.info(f"Full pipeline completed successfully for {subject}")
            return result
            
        except Exception as e:
            logger.error(f"Full pipeline failed for {subject}: {e}")
            raise
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get the current status of pipeline components"""
        return {
            "survey_generation": "implemented",
            "curriculum_generation": "implemented",      # Implemented in subtask 18.3
            "lesson_planning": "implemented",            # Implemented in subtask 18.4
            "content_generation": "implemented",         # Implemented in subtask 18.5
            "rag_system": "implemented",                 # Implemented in subtask 18.2
            "xai_connection": "implemented"
        }   
 
    # Mock methods for testing without API keys
    def _generate_mock_curriculum(self, survey_data: Dict[str, Any], subject: str) -> Dict[str, Any]:
        """Generate mock curriculum for testing"""
        skill_level = survey_data.get('skill_level', 'beginner')
        
        return {
            "curriculum": {
                "subject": subject,
                "skill_level": skill_level,
                "total_lessons": 5,
                "learning_objectives": [
                    f"Understand basic {subject} concepts",
                    f"Apply {subject} techniques in practice",
                    f"Develop {skill_level}-level {subject} skills"
                ],
                "topics": [
                    {
                        "lesson_id": 1,
                        "title": f"Introduction to {subject.title()}",
                        "difficulty": "beginner"
                    },
                    {
                        "lesson_id": 2,
                        "title": f"Core {subject.title()} Concepts",
                        "difficulty": "beginner" if skill_level == "beginner" else "intermediate"
                    },
                    {
                        "lesson_id": 3,
                        "title": f"Practical {subject.title()} Applications",
                        "difficulty": "intermediate"
                    },
                    {
                        "lesson_id": 4,
                        "title": f"Advanced {subject.title()} Techniques",
                        "difficulty": "intermediate" if skill_level == "beginner" else "advanced"
                    },
                    {
                        "lesson_id": 5,
                        "title": f"{subject.title()} Best Practices",
                        "difficulty": "advanced"
                    }
                ]
            },
            "generated_at": "2024-01-15T10:00:00Z",
            "mock_mode": True
        }
    
    def _generate_mock_lesson_plans(self, curriculum_data: Dict[str, Any], subject: str) -> Dict[str, Any]:
        """Generate mock lesson plans for testing"""
        curriculum = curriculum_data.get('curriculum', {})
        topics = curriculum.get('topics', [])
        
        lesson_plans = []
        for topic in topics:
            lesson_plans.append({
                "lesson_id": topic.get('lesson_id'),
                "title": topic.get('title'),
                "difficulty": topic.get('difficulty'),
                "learning_objectives": [
                    f"Learn about {topic.get('title', '').lower()}",
                    f"Practice {subject} skills",
                    "Apply knowledge in exercises"
                ],
                "structure": {
                    "introduction": "5 minutes",
                    "main_content": "15 minutes",
                    "practice": "10 minutes",
                    "summary": "5 minutes"
                },
                "activities": ["Reading", "Examples", "Practice exercises"]
            })
        
        return {
            "lesson_plans": lesson_plans,
            "total_lessons": len(lesson_plans),
            "generated_at": "2024-01-15T10:00:00Z",
            "mock_mode": True
        }
    
    def _generate_mock_lesson_content(self, lesson_plan: Dict[str, Any], subject: str) -> str:
        """Generate mock lesson content for testing"""
        title = lesson_plan.get('title', 'Lesson')
        difficulty = lesson_plan.get('difficulty', 'beginner')
        
        return f"""# {title}

## Learning Objectives
- Understand the fundamentals of {subject}
- Apply {difficulty}-level concepts
- Practice with real-world examples

## Introduction
Welcome to this lesson on {title.lower()}. In this lesson, we'll explore key concepts in {subject} that are appropriate for {difficulty} learners.

## Main Content

### Key Concepts
This is where we would cover the main concepts for {subject}. Since this is a mock lesson generated for testing purposes, the actual content would be generated by the AI system once properly configured.

### Examples
Here are some examples that would help illustrate the concepts:

1. **Example 1**: Basic {subject} application
2. **Example 2**: Intermediate technique
3. **Example 3**: Real-world scenario

## Practice Exercises

### Exercise 1
Try applying what you've learned in this simple exercise.

### Exercise 2
This exercise builds on the previous one with additional complexity.

## Summary
In this lesson, we covered the basics of {title.lower()} in the context of {subject}. The key takeaways are:

- Understanding of core concepts
- Practical application skills
- Foundation for advanced topics

## Next Steps
Continue to the next lesson to build on these concepts.

---
*This is a mock lesson generated for testing purposes. Real lessons would be generated using AI based on your specific learning needs and survey results.*
"""