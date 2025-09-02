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
        # logger.info(f"PROMPT: {prompt}")
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
                logger.info(f"Generation attempt {attempt + 1}/{max_attempts}")
                result = chain.run(**inputs)
                logger.info(f"Generation successful on attempt {attempt + 1}")
                return result
                
            except ValueError as e:
                if "Invalid JSON" in str(e) and attempt < max_attempts - 1:
                    logger.warning(f"JSON parsing failed on attempt {attempt + 1}, retrying: {e}")
                    # For JSON errors, try with slightly different temperature to get different output
                    if hasattr(self, 'llm') and hasattr(self.llm, 'config'):
                        original_temp = self.llm.config.temperature
                        self.llm.config.temperature = min(1.0, original_temp + 0.1 * attempt)
                        logger.info(f"Adjusted temperature to {self.llm.config.temperature} for retry")
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
    
    def __init__(self, temperature: float = 0.7, max_tokens: int = 4000):
        # Use higher token limit for survey generation to prevent truncation
        super().__init__(temperature, max_tokens)
    
    def get_prompt_template(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["subject", "rag_guidelines"],
            template="""
You are an expert educational assessment designer. Create a comprehensive knowledge assessment survey for {subject}.

SUBJECT CONTEXT: {subject} - Focus on creating questions appropriate for this specific field of study.

ASSESSMENT GUIDELINES:
{rag_guidelines}

REQUIREMENTS:
1. Generate exactly 7-8 multiple choice questions
2. Follow the difficulty distribution: 30% beginner, 50% intermediate, 20% advanced
3. Cover core fundamental topics for {subject}
4. Each question must have exactly 4 plausible options
5. Ensure only one option is clearly correct
6. Base incorrect options on common misconceptions
7. Use clear, unambiguous language
8. Include practical scenarios relevant to {subject} when appropriate

DIFFICULTY DEFINITIONS FOR {subject}:
- **Beginner**: Basic terminology, foundational concepts, simple recognition
- **Intermediate**: Concept application, understanding relationships, problem-solving
- **Advanced**: Best practices, complex scenarios, advanced techniques

IMPORTANT: Ensure all questions are directly relevant to {subject} and avoid any programming or technical coding references unless {subject} is specifically about programming.

Return ONLY valid JSON in this exact format:

{{
    "questions": [
        {{
            "id": 1,
            "question": "Question text here",
            "type": "multiple_choice",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "difficulty": "beginner",
            "topic": "topic_name"
        }}
    ],
    "total_questions": 7,
    "subject": "{subject}"
}}

CRITICAL JSON FORMATTING RULES:
1. Return ONLY valid JSON - no additional text before or after
2. Use double quotes for all strings
3. No trailing commas
4. Ensure all brackets and braces are properly closed
5. Create exactly 7 questions for {subject}
6. Do not include any explanatory text outside the JSON

Create questions that effectively assess {subject} knowledge across all skill levels, ensuring all content is appropriate for the {subject} domain.
"""
        )
    
    def generate_survey(self, subject: str, rag_docs: List[str] = None) -> Dict[str, Any]:
        """Generate survey questions for a subject"""
        logger.info(f"Generating LangChain survey for subject: {subject}")
        
        # Load RAG documents if not provided
        if not rag_docs:
            rag_docs = self.load_rag_documents('survey', subject)
        
        # Prepare RAG guidelines
        rag_guidelines = "\n".join(rag_docs) if rag_docs else self._get_default_survey_guidelines()
        logger.info(f"Using RAG guidelines length: {len(rag_guidelines)} characters")
        
        chain = self.create_chain(output_parser=self.json_parser)
        
        inputs = {
            "subject": subject,
            "rag_guidelines": rag_guidelines
        }
        
        logger.info(f"Starting survey generation with max_tokens: {self.llm.config.max_tokens}")
        result = self.generate_with_retry(chain, inputs, max_attempts=3)
        
        # Validate output structure
        expected_keys = ["questions", "total_questions", "subject"]
        if not self.validate_output(result, expected_keys):
            raise ValueError("Generated survey does not have required structure")
        
        # Additional validation for survey quality
        if not self._validate_survey_quality(result):
            raise ValueError("Generated survey does not meet quality standards")
        
        # Add generation metadata
        result['generated_at'] = self._get_current_timestamp()
        result['generation_method'] = 'langchain'
        result['model'] = 'grok-3-mini'
        
        logger.info(f"Successfully generated LangChain survey with {len(result.get('questions', []))} questions")
        return result
    
    def _get_default_survey_guidelines(self) -> str:
        """Get default survey guidelines if RAG documents are not available"""
        return """
        Survey Requirements:
        - Generate 7-8 multiple choice questions
        - Difficulty distribution: 30% beginner, 50% intermediate, 20% advanced
        - Each question has exactly 4 options
        - Only one correct answer per question
        - Cover fundamental topics for the subject
        - Use clear, unambiguous language
        - Base incorrect options on common misconceptions
        """
    
    def _validate_survey_quality(self, survey: Dict[str, Any]) -> bool:
        """Validate survey meets quality standards"""
        questions = survey.get('questions', [])
        
        if not questions or len(questions) < 5 or len(questions) > 10:
            logger.error(f"Invalid question count: {len(questions)}")
            return False
        
        # Check each question structure
        for i, question in enumerate(questions):
            if not self._validate_question_quality(question, i + 1):
                return False
        
        # Check difficulty distribution
        difficulty_counts = {'beginner': 0, 'intermediate': 0, 'advanced': 0}
        for question in questions:
            difficulty = question.get('difficulty', '').lower()
            if difficulty in difficulty_counts:
                difficulty_counts[difficulty] += 1
        
        # Ensure we have questions of different difficulties
        if difficulty_counts['beginner'] == 0 or difficulty_counts['intermediate'] == 0:
            logger.error("Survey must have both beginner and intermediate questions")
            return False
        
        logger.info(f"Survey quality validation passed: {difficulty_counts}")
        return True
    
    def _validate_question_quality(self, question: Dict[str, Any], question_num: int) -> bool:
        """Validate individual question quality"""
        required_fields = ['id', 'question', 'type', 'options', 'correct_answer', 'difficulty', 'topic']
        
        for field in required_fields:
            if field not in question:
                logger.error(f"Question {question_num} missing field: {field}")
                return False
        
        # Validate options
        options = question.get('options', [])
        if not isinstance(options, list) or len(options) != 4:
            logger.error(f"Question {question_num} must have exactly 4 options")
            return False
        
        # Validate correct answer
        correct_answer = question.get('correct_answer')
        if correct_answer not in options:
            logger.error(f"Question {question_num} correct_answer must be one of the options")
            return False
        
        # Validate difficulty
        valid_difficulties = ['beginner', 'intermediate', 'advanced']
        if question.get('difficulty', '').lower() not in valid_difficulties:
            logger.error(f"Question {question_num} has invalid difficulty")
            return False
        
        return True
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

# Placeholder classes for the three-stage pipeline (to be implemented in subsequent subtasks)

class CurriculumGeneratorChain(ContentGenerationChain):
    """Chain for generating curriculum schemes (Stage 1)"""
    
    def __init__(self, temperature: float = 0.7, max_tokens: int = 4000):
        # Use higher token limit for curriculum generation
        super().__init__(temperature, max_tokens)
    
    def get_prompt_template(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["survey_results", "subject", "subject_description", "skill_level", "rag_guidelines", "known_topics"],
            template="""
You are an expert curriculum designer specializing in {subject}. Your role is to create educational content specifically for the subject of {subject}, which is described as: {subject_description}

IMPORTANT: You are creating curriculum for {subject} - {subject_description}. All content must be directly relevant to this subject area and its description. Do NOT create programming or coding content unless the subject is specifically about programming.

TASK: Create a 5-lesson curriculum for {subject} at {skill_level} level.

SUBJECT DETAILS:
- Subject: {subject}
- Description: {subject_description}
- Target Level: {skill_level}

SURVEY ANALYSIS:
{survey_results}

CURRICULUM REQUIREMENTS:
1. Create exactly 5 lessons that build upon each other
2. Each lesson should be appropriate for the {skill_level} level
3. All content must relate directly to: {subject_description}
4. Ensure lessons are practical and applicable to the subject area
5. Progress from foundational concepts to more advanced applications

Return ONLY valid JSON in this exact format:

{{
    "curriculum": {{
        "subject": "{subject}",
        "skill_level": "{skill_level}",
        "total_lessons": 5,
        "learning_objectives": [
            "First learning objective for {subject}",
            "Second learning objective for {subject}",
            "Third learning objective for {subject}"
        ],
        "topics": [
            {{
                "lesson_id": 1,
                "title": "Lesson 1 title",
                "difficulty": "beginner",
                "topics": ["topic 1", "topic 2"],
                "estimated_duration": "60 minutes"
            }},
            {{
                "lesson_id": 2,
                "title": "Lesson 2 title",
                "difficulty": "beginner",
                "topics": ["topic 1", "topic 2"],
                "estimated_duration": "60 minutes"
            }},
            {{
                "lesson_id": 3,
                "title": "Lesson 3 title",
                "difficulty": "intermediate",
                "topics": ["topic 1", "topic 2"],
                "estimated_duration": "75 minutes"
            }},
            {{
                "lesson_id": 4,
                "title": "Lesson 4 title",
                "difficulty": "intermediate",
                "topics": ["topic 1", "topic 2"],
                "estimated_duration": "75 minutes"
            }},
            {{
                "lesson_id": 5,
                "title": "Lesson 5 title",
                "difficulty": "advanced",
                "topics": ["topic 1", "topic 2"],
                "estimated_duration": "90 minutes"
            }}
        ]
    }},
    "generated_at": "2024-01-15T10:00:00Z",
    "generation_stage": "curriculum_complete"
}}

CRITICAL JSON FORMATTING RULES:
1. Return ONLY valid JSON - no additional text before or after
2. Use double quotes for all strings
3. No trailing commas
4. Ensure all brackets and braces are properly closed
5. Replace the example content with actual curriculum for {subject}
6. Do not include any explanatory text outside the JSON

Remember: You are creating curriculum for {subject} which is {subject_description}. Ensure all lesson titles, topics, and objectives are directly relevant to this subject area.
"""
        )
    
    def generate_curriculum(self, survey_data: Dict[str, Any], subject: str, rag_docs: List[str] = None) -> Dict[str, Any]:
        """Generate curriculum scheme based on survey results"""
        logger.info(f"Starting curriculum generation for {subject}")
        
        # Get subject description
        subject_description = self._get_subject_description(subject)
        
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
            "subject_description": subject_description,
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
        curriculum_keys = ["subject", "skill_level", "total_lessons", "topics"]
        if not self.validate_output(curriculum, curriculum_keys):
            raise ValueError("Generated curriculum structure is invalid")
        
        # Validate that we have exactly 5 lessons
        topics = curriculum.get("topics", [])
        if len(topics) != 5:
            logger.warning(f"Expected 5 lessons, got {len(topics)}. Adjusting...")
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
    
    def _get_subject_description(self, subject: str) -> str:
        """Get subject description from AVAILABLE_SUBJECTS configuration"""
        try:
            # Import AVAILABLE_SUBJECTS from the subjects API
            from app.api.subjects import AVAILABLE_SUBJECTS
            
            if subject in AVAILABLE_SUBJECTS:
                description = AVAILABLE_SUBJECTS[subject].get('description', '')
                if description:
                    logger.debug(f"Found subject description for {subject}: {description}")
                    return description
            
            # Fallback description if not found
            logger.warning(f"No description found for subject {subject}, using generic description")
            return f"Educational content related to {subject}"
            
        except ImportError as e:
            logger.error(f"Could not import AVAILABLE_SUBJECTS: {e}")
            return f"Educational content related to {subject}"
        except Exception as e:
            logger.error(f"Error getting subject description for {subject}: {e}")
            return f"Educational content related to {subject}"

class LessonPlannerChain(ContentGenerationChain):
    """Chain for generating lesson plans (Stage 2)"""
    
    def __init__(self, temperature: float = 0.7, max_tokens: int = 5000):
        # Use higher token limit for lesson planning to prevent truncation
        super().__init__(temperature, max_tokens)
    
    def get_prompt_template(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["curriculum_data", "subject", "subject_description", "skill_level", "rag_guidelines"],
            template="""
You are an expert lesson planner for {subject}: {subject_description}

Create detailed lesson plans for {subject} at {skill_level} level.

CURRICULUM: {curriculum_data}

REQUIREMENTS:
- All content must relate to {subject_description}
- Include learning objectives and activities
- Structure lessons with clear time allocation
- Focus on practical skills for {subject_description}

Return ONLY valid JSON in this exact format:

{{
    "lesson_plans": [
        {{
            "lesson_id": 1,
            "title": "Lesson title here",
            "learning_objectives": [
                "First learning objective",
                "Second learning objective"
            ],
            "key_concepts": [
                "First key concept",
                "Second key concept"
            ],
            "activities": [
                "First activity",
                "Second activity"
            ],
            "structure": {{
                "introduction": "10 minutes",
                "main_content": "35 minutes",
                "practice": "10 minutes",
                "summary": "5 minutes"
            }}
        }}
    ],
    "generated_at": "2024-01-15T10:00:00Z",
    "generation_stage": "lesson_plans_complete"
}}

CRITICAL JSON FORMATTING RULES:
1. Return ONLY valid JSON - no additional text before or after
2. Use double quotes for all strings
3. No trailing commas
4. Ensure all brackets and braces are properly closed
5. Replace the example content with actual lesson plans for {subject}
6. Do not include any explanatory text outside the JSON

REMEMBER: You are creating lesson plans for {subject} which is {subject_description}. Every lesson plan element should be directly relevant to this subject area and avoid any programming references unless specifically about programming.
"""
        )
    
    def generate_lesson_plans(self, curriculum_data: Dict[str, Any], subject: str, rag_docs: List[str] = None) -> Dict[str, Any]:
        """Generate detailed lesson plans based on curriculum"""
        logger.info(f"Starting lesson plan generation for {subject}")
        
        # Get subject description
        subject_description = self._get_subject_description(subject)
        
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
            "subject_description": subject_description,
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
            lesson_keys = ["lesson_id", "title"]
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
    
    def _get_subject_description(self, subject: str) -> str:
        """Get subject description from AVAILABLE_SUBJECTS configuration"""
        try:
            # Import AVAILABLE_SUBJECTS from the subjects API
            from app.api.subjects import AVAILABLE_SUBJECTS
            
            if subject in AVAILABLE_SUBJECTS:
                description = AVAILABLE_SUBJECTS[subject].get('description', '')
                if description:
                    logger.debug(f"Found subject description for {subject}: {description}")
                    return description
            
            # Fallback description if not found
            logger.warning(f"No description found for subject {subject}, using generic description")
            return f"Educational content related to {subject}"
            
        except ImportError as e:
            logger.error(f"Could not import AVAILABLE_SUBJECTS: {e}")
            return f"Educational content related to {subject}"
        except Exception as e:
            logger.error(f"Error getting subject description for {subject}: {e}")
            return f"Educational content related to {subject}"

class ContentGeneratorChain(ContentGenerationChain):
    """Chain for generating lesson content (Stage 3)"""
    
    def __init__(self, temperature: float = 0.7, max_tokens: int = 6000):
        # Use higher token limit for content generation (longest output)
        super().__init__(temperature, max_tokens)
    
    def get_prompt_template(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["lesson_plan", "subject", "subject_description", "skill_level", "rag_guidelines"],
            template="""
You are an expert educator and content creator specializing in {subject}. Your role is to write educational lesson content specifically for the subject of {subject}, which is described as: {subject_description}

CRITICAL INSTRUCTIONS:
- You are creating content for {subject} - {subject_description}
- ALL content must be directly relevant to this subject area and description
- Do NOT include programming, coding, or technical software content unless the subject is specifically about programming
- Focus on the actual subject matter as described: {subject_description}

SUBJECT DETAILS:
- Subject: {subject}
- Description: {subject_description}
- Target Level: {skill_level}

LESSON PLAN TO IMPLEMENT:
{lesson_plan}

CONTENT GUIDELINES:
{rag_guidelines}

REQUIREMENTS:
1. Write clear explanations of key concepts that are specifically relevant to {subject_description}
2. Include 1-2 practical examples that demonstrate real-world applications of {subject_description}
3. Create 2-3 exercises that help learners practice {subject} skills as described in: {subject_description}
4. Use markdown formatting for clear structure
5. Keep content focused and directly applicable to {subject_description}
6. Ensure every paragraph relates back to the core subject: {subject_description}

CONTENT STRUCTURE:
# [Lesson Title - relevant to {subject}]

## Introduction
Brief introduction explaining how this lesson relates to {subject_description}

## Key Concepts
Core concepts specific to {subject_description}

## Practical Example
Real-world example demonstrating {subject_description} in action

## Practice Exercises
Hands-on activities that apply {subject_description} principles

## Summary
Key takeaways relevant to {subject_description}

REMEMBER: You are creating educational content for {subject} which is {subject_description}. Every sentence should be relevant to this subject area. Avoid any programming or technical coding references unless the subject description specifically mentions programming or software development.

Generate comprehensive lesson content in markdown format.
"""
        )
    
    def generate_content(self, lesson_plan: Dict[str, Any], subject: str, rag_docs: List[str] = None) -> str:
        """Generate complete lesson content based on lesson plan"""
        lesson_id = lesson_plan.get("lesson_id", "unknown")
        lesson_title = lesson_plan.get("title", "Untitled Lesson")
        
        logger.info(f"Starting content generation for lesson {lesson_id}: {lesson_title}")
        
        # Get subject description from AVAILABLE_SUBJECTS
        subject_description = self._get_subject_description(subject)
        
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
            "subject_description": subject_description,
            "skill_level": skill_level,
            "rag_guidelines": rag_guidelines
        }
        
        logger.info(f"Sending content generation request for lesson {lesson_id} with {len(str(inputs))} chars of input")
        result = self.generate_with_retry(chain, inputs)
        
        # Validate that we got content
        if not result or len(result.strip()) < 100:
            logger.error(f"Generated content too short: {len(result) if result else 0} characters")
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
    
    def _get_subject_description(self, subject: str) -> str:
        """Get subject description from AVAILABLE_SUBJECTS configuration"""
        try:
            # Import AVAILABLE_SUBJECTS from the subjects API
            from app.api.subjects import AVAILABLE_SUBJECTS
            
            if subject in AVAILABLE_SUBJECTS:
                description = AVAILABLE_SUBJECTS[subject].get('description', '')
                if description:
                    logger.debug(f"Found subject description for {subject}: {description}")
                    return description
            
            # Fallback description if not found
            logger.warning(f"No description found for subject {subject}, using generic description")
            return f"Educational content related to {subject}"
            
        except ImportError as e:
            logger.error(f"Could not import AVAILABLE_SUBJECTS: {e}")
            return f"Educational content related to {subject}"
        except Exception as e:
            logger.error(f"Error getting subject description for {subject}: {e}")
            return f"Educational content related to {subject}"