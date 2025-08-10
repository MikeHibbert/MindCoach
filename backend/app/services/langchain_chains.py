"""
Base LangChain chain classes for content generation
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from .langchain_base import XAILLM, JSONOutputParser, MarkdownOutputParser, validate_environment

logger = logging.getLogger(__name__)

class BaseLangChainService(ABC):
    """Base class for all LangChain-powered services"""
    
    def __init__(self, temperature: float = 0.7, max_tokens: int = 2000):
        """Initialize the base service with LLM configuration"""
        validate_environment()
        
        self.llm = XAILLM(
            temperature=temperature,
            max_tokens=max_tokens
        )
        self.json_parser = JSONOutputParser()
        self.markdown_parser = MarkdownOutputParser()
        
        logger.info(f"Initialized {self.__class__.__name__} with temperature={temperature}, max_tokens={max_tokens}")
    
    @abstractmethod
    def get_prompt_template(self) -> PromptTemplate:
        """Get the prompt template for this service"""
        pass
    
    def create_chain(self, output_parser=None) -> LLMChain:
        """Create a LangChain chain with the prompt template"""
        prompt = self.get_prompt_template()
        chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            output_parser=output_parser
        )
        return chain
    
    def generate_with_retry(self, chain: LLMChain, inputs: Dict[str, Any], max_attempts: int = 3) -> Any:
        """Generate content with retry logic for parsing errors"""
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logger.debug(f"Generation attempt {attempt + 1}/{max_attempts}")
                result = chain.run(**inputs)
                logger.debug(f"Generation successful on attempt {attempt + 1}")
                return result
                
            except ValueError as e:
                if "Invalid JSON" in str(e) and attempt < max_attempts - 1:
                    logger.warning(f"JSON parsing failed on attempt {attempt + 1}, retrying: {e}")
                    last_error = e
                    continue
                else:
                    raise e
            except Exception as e:
                logger.error(f"Generation failed on attempt {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    last_error = e
                    continue
                else:
                    raise e
        
        # All attempts failed
        error_msg = f"All {max_attempts} generation attempts failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)

class ContentGenerationChain(BaseLangChainService):
    """Base class for content generation chains"""
    
    def __init__(self, temperature: float = 0.7, max_tokens: int = 3000):
        super().__init__(temperature, max_tokens)
    
    def load_rag_documents(self, doc_type: str, subject: str = None) -> List[str]:
        """Load RAG documents for guidance"""
        from .rag_document_service import rag_service
        logger.debug(f"Loading RAG documents for type: {doc_type}, subject: {subject}")
        return rag_service.load_documents_for_stage(doc_type, subject)
    
    def validate_output(self, output: Any, expected_keys: List[str] = None) -> bool:
        """Validate generated output structure"""
        if expected_keys and isinstance(output, dict):
            missing_keys = [key for key in expected_keys if key not in output]
            if missing_keys:
                logger.error(f"Missing required keys in output: {missing_keys}")
                return False
        
        logger.debug("Output validation passed")
        return True

class SurveyGenerationChain(ContentGenerationChain):
    """Chain for generating survey questions"""
    
    def get_prompt_template(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["subject", "rag_guidelines"],
            template="""
You are an expert educational content creator. Generate a knowledge assessment survey for the subject: {subject}

Guidelines to follow:
{rag_guidelines}

Create 5-10 multiple choice questions that assess different skill levels (beginner, intermediate, advanced).
Each question should help determine the learner's current knowledge level.

Return your response as a JSON object with this exact structure:
{{
    "questions": [
        {{
            "id": 1,
            "question": "Question text here",
            "type": "multiple_choice",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "difficulty": "beginner|intermediate|advanced",
            "topic": "specific topic this question covers"
        }}
    ],
    "total_questions": 5,
    "subject": "{subject}"
}}

Ensure questions cover a range of topics and difficulty levels for comprehensive assessment.
"""
        )
    
    def generate_survey(self, subject: str, rag_docs: List[str] = None) -> Dict[str, Any]:
        """Generate survey questions for a subject"""
        logger.info(f"Generating survey for subject: {subject}")
        
        rag_guidelines = "\n".join(rag_docs) if rag_docs else "Create clear, unambiguous questions with one correct answer."
        
        chain = self.create_chain(output_parser=self.json_parser)
        
        inputs = {
            "subject": subject,
            "rag_guidelines": rag_guidelines
        }
        
        result = self.generate_with_retry(chain, inputs)
        
        # Validate output structure
        expected_keys = ["questions", "total_questions", "subject"]
        if not self.validate_output(result, expected_keys):
            raise ValueError("Generated survey does not have required structure")
        
        logger.info(f"Successfully generated survey with {len(result.get('questions', []))} questions")
        return result

# Placeholder classes for the three-stage pipeline (to be implemented in subsequent subtasks)

class CurriculumGeneratorChain(ContentGenerationChain):
    """Chain for generating curriculum schemes (Stage 1)"""
    
    def get_prompt_template(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["survey_results", "subject", "skill_level", "rag_guidelines", "known_topics"],
            template="""
You are an expert educational curriculum designer. Create a comprehensive 10-lesson learning curriculum for {subject} based on the learner's assessment results.

LEARNER ASSESSMENT:
{survey_results}

SKILL LEVEL: {skill_level}

CURRICULUM GUIDELINES:
{rag_guidelines}

TOPICS TO SKIP (learner already knows):
{known_topics}

REQUIREMENTS:
1. Create exactly 10 lessons that build progressively
2. Adapt difficulty and pacing based on the learner's skill level
3. Skip topics the learner already demonstrated knowledge of
4. Replace skipped beginner topics with more advanced material if skill level is higher
5. Each lesson should take 45-60 minutes to complete
6. Include clear learning objectives for the overall curriculum

Return your response as a JSON object with this exact structure:
{{
    "curriculum": {{
        "subject": "{subject}",
        "skill_level": "{skill_level}",
        "total_lessons": 10,
        "learning_objectives": [
            "High-level learning goal 1",
            "High-level learning goal 2",
            "High-level learning goal 3"
        ],
        "topics": [
            {{
                "lesson_id": 1,
                "title": "Descriptive Lesson Title",
                "topics": ["topic1", "topic2", "topic3"],
                "prerequisites": ["previous_topic_if_any"],
                "difficulty": "beginner|intermediate|advanced",
                "estimated_duration": "45-60 minutes"
            }}
        ]
    }},
    "generated_at": "2024-01-15T10:00:00Z",
    "generation_stage": "curriculum_complete"
}}

Ensure the curriculum provides a logical learning progression and covers all essential topics for {subject} at the {skill_level} level.
"""
        )
    
    def generate_curriculum(self, survey_data: Dict[str, Any], subject: str, rag_docs: List[str] = None) -> Dict[str, Any]:
        """Generate curriculum scheme based on survey results"""
        logger.info(f"Starting curriculum generation for {subject}")
        
        # Extract skill level from survey data
        skill_level = survey_data.get('skill_level', 'intermediate')
        
        # Determine known topics from survey answers
        known_topics = self._extract_known_topics(survey_data)
        
        # Prepare RAG guidelines
        rag_guidelines = "\n".join(rag_docs) if rag_docs else "Create a comprehensive, well-structured curriculum with clear progression."
        
        # Format survey results for the prompt
        survey_summary = self._format_survey_results(survey_data)
        
        chain = self.create_chain(output_parser=self.json_parser)
        
        inputs = {
            "survey_results": survey_summary,
            "subject": subject,
            "skill_level": skill_level,
            "rag_guidelines": rag_guidelines,
            "known_topics": ", ".join(known_topics) if known_topics else "None identified"
        }
        
        result = self.generate_with_retry(chain, inputs)
        
        # Validate output structure
        expected_keys = ["curriculum"]
        if not self.validate_output(result, expected_keys):
            raise ValueError("Generated curriculum does not have required structure")
        
        # Validate curriculum structure
        curriculum = result.get("curriculum", {})
        curriculum_keys = ["subject", "skill_level", "total_lessons", "learning_objectives", "topics"]
        if not self.validate_output(curriculum, curriculum_keys):
            raise ValueError("Generated curriculum structure is invalid")
        
        # Validate that we have exactly 10 lessons
        topics = curriculum.get("topics", [])
        if len(topics) != 10:
            logger.warning(f"Expected 10 lessons, got {len(topics)}. Adjusting...")
            # Could implement logic to adjust lesson count here
        
        logger.info(f"Successfully generated curriculum with {len(topics)} lessons for {subject}")
        return result
    
    def _extract_known_topics(self, survey_data: Dict[str, Any]) -> List[str]:
        """Extract topics the learner already knows from survey results"""
        known_topics = []
        
        answers = survey_data.get('answers', [])
        for answer in answers:
            if answer.get('correct', False):
                topic = answer.get('topic')
                if topic and topic not in known_topics:
                    known_topics.append(topic)
        
        return known_topics
    
    def _format_survey_results(self, survey_data: Dict[str, Any]) -> str:
        """Format survey results for inclusion in the prompt"""
        skill_level = survey_data.get('skill_level', 'unknown')
        answers = survey_data.get('answers', [])
        
        correct_count = sum(1 for answer in answers if answer.get('correct', False))
        total_count = len(answers)
        percentage = (correct_count / total_count * 100) if total_count > 0 else 0
        
        summary = f"Skill Level: {skill_level}\n"
        summary += f"Survey Performance: {correct_count}/{total_count} correct ({percentage:.1f}%)\n"
        
        if answers:
            summary += "Topic Performance:\n"
            topic_performance = {}
            for answer in answers:
                topic = answer.get('topic', 'unknown')
                correct = answer.get('correct', False)
                if topic not in topic_performance:
                    topic_performance[topic] = {'correct': 0, 'total': 0}
                topic_performance[topic]['total'] += 1
                if correct:
                    topic_performance[topic]['correct'] += 1
            
            for topic, perf in topic_performance.items():
                percentage = (perf['correct'] / perf['total'] * 100) if perf['total'] > 0 else 0
                summary += f"- {topic}: {perf['correct']}/{perf['total']} ({percentage:.1f}%)\n"
        
        return summary

class LessonPlannerChain(ContentGenerationChain):
    """Chain for generating lesson plans (Stage 2)"""
    
    def get_prompt_template(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["curriculum_data", "subject", "skill_level", "rag_guidelines"],
            template="""
You are an expert educational lesson planner. Create detailed lesson plans for each lesson in the provided curriculum.

CURRICULUM DATA:
{curriculum_data}

SUBJECT: {subject}
SKILL LEVEL: {skill_level}

LESSON PLANNING GUIDELINES:
{rag_guidelines}

REQUIREMENTS:
1. Create a detailed lesson plan for each lesson in the curriculum
2. Each lesson should be structured for 60 minutes of learning
3. Include specific learning objectives for each lesson
4. Define clear activities and time allocations
5. Specify assessment methods for each lesson
6. Include materials needed and key concepts
7. Ensure logical progression between lessons

Return your response as a JSON object with this exact structure:
{{
    "lesson_plans": [
        {{
            "lesson_id": 1,
            "title": "Lesson Title from Curriculum",
            "learning_objectives": [
                "Specific, measurable objective 1",
                "Specific, measurable objective 2",
                "Specific, measurable objective 3"
            ],
            "structure": {{
                "introduction": "5 minutes",
                "main_content": "25 minutes",
                "examples": "15 minutes", 
                "exercises": "15 minutes",
                "summary": "5 minutes"
            }},
            "activities": [
                "Interactive demonstration of key concepts",
                "Guided practice with step-by-step examples",
                "Independent coding challenges",
                "Peer review and discussion"
            ],
            "assessment": "Description of how learning will be assessed (coding exercises, quizzes, projects)",
            "materials_needed": [
                "Code editor or IDE",
                "Specific libraries or tools",
                "Reference documentation"
            ],
            "key_concepts": [
                "concept1",
                "concept2", 
                "concept3"
            ]
        }}
    ],
    "generated_at": "2024-01-15T10:00:00Z",
    "generation_stage": "lesson_plans_complete"
}}

Create comprehensive lesson plans that will effectively teach the {subject} curriculum at the {skill_level} level.
"""
        )
    
    def generate_lesson_plans(self, curriculum_data: Dict[str, Any], subject: str, rag_docs: List[str] = None) -> Dict[str, Any]:
        """Generate detailed lesson plans based on curriculum"""
        logger.info(f"Starting lesson plan generation for {subject}")
        
        # Extract curriculum information
        curriculum = curriculum_data.get("curriculum", {})
        skill_level = curriculum.get("skill_level", "intermediate")
        topics = curriculum.get("topics", [])
        
        if not topics:
            raise ValueError("No topics found in curriculum data")
        
        # Prepare RAG guidelines
        rag_guidelines = "\n".join(rag_docs) if rag_docs else "Create detailed, structured lesson plans with clear objectives and activities."
        
        # Format curriculum data for the prompt
        curriculum_summary = self._format_curriculum_data(curriculum_data)
        
        chain = self.create_chain(output_parser=self.json_parser)
        
        inputs = {
            "curriculum_data": curriculum_summary,
            "subject": subject,
            "skill_level": skill_level,
            "rag_guidelines": rag_guidelines
        }
        
        result = self.generate_with_retry(chain, inputs)
        
        # Validate output structure
        expected_keys = ["lesson_plans"]
        if not self.validate_output(result, expected_keys):
            raise ValueError("Generated lesson plans do not have required structure")
        
        # Validate lesson plans structure
        lesson_plans = result.get("lesson_plans", [])
        if not lesson_plans:
            raise ValueError("No lesson plans generated")
        
        # Validate each lesson plan
        for i, lesson_plan in enumerate(lesson_plans):
            lesson_keys = ["lesson_id", "title", "learning_objectives", "structure", "activities", "assessment"]
            if not self.validate_output(lesson_plan, lesson_keys):
                raise ValueError(f"Lesson plan {i+1} has invalid structure")
        
        # Validate that we have lesson plans for all curriculum topics
        expected_lesson_count = len(topics)
        actual_lesson_count = len(lesson_plans)
        if actual_lesson_count != expected_lesson_count:
            logger.warning(f"Expected {expected_lesson_count} lesson plans, got {actual_lesson_count}")
        
        logger.info(f"Successfully generated {len(lesson_plans)} lesson plans for {subject}")
        return result
    
    def _format_curriculum_data(self, curriculum_data: Dict[str, Any]) -> str:
        """Format curriculum data for inclusion in the prompt"""
        curriculum = curriculum_data.get("curriculum", {})
        
        summary = f"Subject: {curriculum.get('subject', 'Unknown')}\n"
        summary += f"Skill Level: {curriculum.get('skill_level', 'Unknown')}\n"
        summary += f"Total Lessons: {curriculum.get('total_lessons', 0)}\n\n"
        
        summary += "Learning Objectives:\n"
        for obj in curriculum.get("learning_objectives", []):
            summary += f"- {obj}\n"
        
        summary += "\nLesson Topics:\n"
        for topic in curriculum.get("topics", []):
            lesson_id = topic.get("lesson_id", "?")
            title = topic.get("title", "Untitled")
            topics_list = ", ".join(topic.get("topics", []))
            difficulty = topic.get("difficulty", "unknown")
            duration = topic.get("estimated_duration", "60 minutes")
            
            summary += f"Lesson {lesson_id}: {title}\n"
            summary += f"  Topics: {topics_list}\n"
            summary += f"  Difficulty: {difficulty}\n"
            summary += f"  Duration: {duration}\n"
            
            prerequisites = topic.get("prerequisites", [])
            if prerequisites:
                summary += f"  Prerequisites: {', '.join(prerequisites)}\n"
            summary += "\n"
        
        return summary

class ContentGeneratorChain(ContentGenerationChain):
    """Chain for generating lesson content (Stage 3)"""
    
    def get_prompt_template(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["lesson_plan", "subject", "skill_level", "rag_guidelines"],
            template="""
You are an expert educational content creator. Generate complete lesson content based on the provided lesson plan.

LESSON PLAN:
{lesson_plan}

SUBJECT: {subject}
SKILL LEVEL: {skill_level}

CONTENT GUIDELINES:
{rag_guidelines}

REQUIREMENTS:
1. Create comprehensive lesson content following the lesson plan structure
2. Include clear explanations of all key concepts
3. Provide exactly 2 practical code examples with detailed explanations
4. Create 3-5 hands-on exercises of varying difficulty
5. Include proper markdown formatting with headers, code blocks, and lists
6. Ensure content is appropriate for the {skill_level} skill level
7. Make content engaging and educational

CONTENT STRUCTURE:
- Introduction (connect to learning objectives)
- Core Concepts (detailed explanations)
- Code Examples (2 practical examples with explanations)
- Hands-on Exercises (3-5 exercises with instructions)
- Summary and Next Steps

Return your response as properly formatted markdown content. Do not include JSON structure - just return the markdown content directly.

Generate engaging, comprehensive lesson content that effectively teaches the concepts outlined in the lesson plan.
"""
        )
    
    def generate_content(self, lesson_plan: Dict[str, Any], subject: str, rag_docs: List[str] = None) -> str:
        """Generate complete lesson content based on lesson plan"""
        lesson_id = lesson_plan.get("lesson_id", "unknown")
        lesson_title = lesson_plan.get("title", "Untitled Lesson")
        
        logger.info(f"Starting content generation for lesson {lesson_id}: {lesson_title}")
        
        # Extract lesson information
        learning_objectives = lesson_plan.get("learning_objectives", [])
        key_concepts = lesson_plan.get("key_concepts", [])
        activities = lesson_plan.get("activities", [])
        
        # Determine skill level (try to extract from lesson plan or use default)
        skill_level = "intermediate"  # Default
        if "difficulty" in lesson_plan:
            skill_level = lesson_plan["difficulty"]
        
        # Prepare RAG guidelines
        rag_guidelines = "\n".join(rag_docs) if rag_docs else "Create clear, engaging content with practical examples and exercises."
        
        # Format lesson plan for the prompt
        lesson_plan_summary = self._format_lesson_plan(lesson_plan)
        
        chain = self.create_chain(output_parser=self.markdown_parser)
        
        inputs = {
            "lesson_plan": lesson_plan_summary,
            "subject": subject,
            "skill_level": skill_level,
            "rag_guidelines": rag_guidelines
        }
        
        result = self.generate_with_retry(chain, inputs)
        
        # Validate that we got content
        if not result or len(result.strip()) < 100:
            raise ValueError("Generated content is too short or empty")
        
        # Basic content validation
        if not self._validate_content_structure(result):
            logger.warning("Generated content may not follow expected structure")
        
        logger.info(f"Successfully generated content for lesson {lesson_id} ({len(result)} characters)")
        return result
    
    def _format_lesson_plan(self, lesson_plan: Dict[str, Any]) -> str:
        """Format lesson plan data for inclusion in the prompt"""
        lesson_id = lesson_plan.get("lesson_id", "?")
        title = lesson_plan.get("title", "Untitled")
        
        summary = f"Lesson {lesson_id}: {title}\n\n"
        
        # Learning objectives
        objectives = lesson_plan.get("learning_objectives", [])
        if objectives:
            summary += "Learning Objectives:\n"
            for obj in objectives:
                summary += f"- {obj}\n"
            summary += "\n"
        
        # Time structure
        structure = lesson_plan.get("structure", {})
        if structure:
            summary += "Time Allocation:\n"
            for section, time in structure.items():
                summary += f"- {section.replace('_', ' ').title()}: {time}\n"
            summary += "\n"
        
        # Activities
        activities = lesson_plan.get("activities", [])
        if activities:
            summary += "Planned Activities:\n"
            for activity in activities:
                summary += f"- {activity}\n"
            summary += "\n"
        
        # Key concepts
        key_concepts = lesson_plan.get("key_concepts", [])
        if key_concepts:
            summary += "Key Concepts to Cover:\n"
            for concept in key_concepts:
                summary += f"- {concept}\n"
            summary += "\n"
        
        # Assessment
        assessment = lesson_plan.get("assessment", "")
        if assessment:
            summary += f"Assessment Method: {assessment}\n\n"
        
        # Materials needed
        materials = lesson_plan.get("materials_needed", [])
        if materials:
            summary += "Materials Needed:\n"
            for material in materials:
                summary += f"- {material}\n"
            summary += "\n"
        
        return summary
    
    def _validate_content_structure(self, content: str) -> bool:
        """Validate that generated content has expected structure"""
        content_lower = content.lower()
        
        # Check for basic markdown structure
        has_headers = '#' in content
        has_code_blocks = '```' in content
        has_lists = ('- ' in content or '1. ' in content)
        
        # Check for expected sections
        has_introduction = any(word in content_lower for word in ['introduction', 'overview', 'welcome'])
        has_examples = any(word in content_lower for word in ['example', 'demonstration'])
        has_exercises = any(word in content_lower for word in ['exercise', 'practice', 'challenge'])
        has_summary = any(word in content_lower for word in ['summary', 'conclusion', 'recap'])
        
        structure_score = sum([
            has_headers, has_code_blocks, has_lists,
            has_introduction, has_examples, has_exercises, has_summary
        ])
        
        # Consider valid if at least 4 out of 7 structure elements are present
        is_valid = structure_score >= 4
        
        if not is_valid:
            logger.warning(f"Content structure validation failed. Score: {structure_score}/7")
        
        return is_valid