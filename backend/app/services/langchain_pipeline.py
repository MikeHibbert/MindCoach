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
        validate_environment()
        
        # Initialize all chain components
        self.survey_chain = SurveyGenerationChain(temperature=0.8, max_tokens=2000)
        self.curriculum_chain = CurriculumGeneratorChain(temperature=0.7, max_tokens=3000)
        self.lesson_planner_chain = LessonPlannerChain(temperature=0.7, max_tokens=3000)
        self.content_generator_chain = ContentGeneratorChain(temperature=0.6, max_tokens=4000)
        
        logger.info("LangChain pipeline service initialized")
    
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
        
        try:
            result = self.curriculum_chain.generate_curriculum(survey_data, subject, rag_docs)
            logger.info(f"Stage 1 completed: Curriculum generated for {subject}")
            return result
            
        except Exception as e:
            logger.error(f"Stage 1 failed: Curriculum generation error for {subject}: {e}")
            raise
    
    def generate_lesson_plans(self, curriculum_data: Dict[str, Any], subject: str, rag_docs: List[str] = None) -> Dict[str, Any]:
        """Stage 2: Generate lesson plans based on curriculum"""
        logger.info(f"Starting Stage 2: Lesson planning for {subject}")
        
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