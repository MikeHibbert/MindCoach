"""
Survey analysis service for processing survey answers and determining skill levels
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging

from app.services.survey_generation_service import SurveyGenerationService
from app.services.survey_result_service import SurveyResultService
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

class SurveyAnalysisService:
    """Service for analyzing survey responses and determining user skill levels"""
    
    # Skill level thresholds based on percentage of correct answers
    SKILL_LEVEL_THRESHOLDS = {
        'beginner': 0.0,      # 0-49% correct
        'intermediate': 0.5,   # 50-74% correct  
        'advanced': 0.75       # 75%+ correct
    }
    
    # Difficulty weights for scoring
    DIFFICULTY_WEIGHTS = {
        'beginner': 1.0,
        'intermediate': 1.5,
        'advanced': 2.0
    }
    
    @classmethod
    def process_survey_answers(cls, user_id: str, subject: str, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process survey answers and determine user skill level
        
        Args:
            user_id: The user ID
            subject: The subject being surveyed
            answers: List of answer dictionaries with question_id and answer
            
        Returns:
            Dictionary containing analysis results
            
        Raises:
            ValueError: If survey or answers are invalid
            FileNotFoundError: If survey file doesn't exist
        """
        logger.info(f"Processing survey answers for user {user_id}, subject {subject}")
        
        # Load the original survey to validate answers
        survey = cls._load_survey(user_id, subject)
        if not survey:
            raise FileNotFoundError(f"Survey not found for user {user_id}, subject {subject}")
        
        # Validate answers format
        cls._validate_answers(answers, survey)
        
        # Process each answer and calculate scores
        processed_answers = []
        correct_count = 0
        total_weighted_score = 0
        max_weighted_score = 0
        topic_performance = {}
        difficulty_performance = {'beginner': {'correct': 0, 'total': 0},
                                'intermediate': {'correct': 0, 'total': 0},
                                'advanced': {'correct': 0, 'total': 0}}
        
        # Create question lookup for efficiency
        question_lookup = {q['id']: q for q in survey['questions']}
        
        for answer in answers:
            question_id = answer['question_id']
            user_answer = answer['answer']
            
            if question_id not in question_lookup:
                logger.warning(f"Question ID {question_id} not found in survey")
                continue
            
            question = question_lookup[question_id]
            correct_answer = question['correct_answer']
            difficulty = question['difficulty']
            topic = question['topic']
            weight = cls.DIFFICULTY_WEIGHTS[difficulty]
            
            # Check if answer is correct
            is_correct = user_answer == correct_answer
            if is_correct:
                correct_count += 1
                total_weighted_score += weight
            
            max_weighted_score += weight
            
            # Track performance by topic
            if topic not in topic_performance:
                topic_performance[topic] = {'correct': 0, 'total': 0}
            topic_performance[topic]['total'] += 1
            if is_correct:
                topic_performance[topic]['correct'] += 1
            
            # Track performance by difficulty
            difficulty_performance[difficulty]['total'] += 1
            if is_correct:
                difficulty_performance[difficulty]['correct'] += 1
            
            # Store processed answer
            processed_answers.append({
                'question_id': question_id,
                'question': question['question'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'difficulty': difficulty,
                'topic': topic,
                'weight': weight
            })
        
        # Calculate overall performance metrics
        total_questions = len(answers)
        accuracy = correct_count / total_questions if total_questions > 0 else 0
        weighted_accuracy = total_weighted_score / max_weighted_score if max_weighted_score > 0 else 0
        
        # Determine skill level based on weighted accuracy
        skill_level = cls._determine_skill_level(weighted_accuracy, difficulty_performance)
        
        # Calculate topic strengths and weaknesses
        topic_analysis = cls._analyze_topic_performance(topic_performance)
        
        # Create analysis results
        analysis_results = {
            'user_id': user_id,
            'subject': subject,
            'processed_at': datetime.utcnow().isoformat(),
            'total_questions': total_questions,
            'correct_answers': correct_count,
            'accuracy': accuracy,
            'weighted_accuracy': weighted_accuracy,
            'skill_level': skill_level,
            'performance_by_difficulty': difficulty_performance,
            'topic_analysis': topic_analysis,
            'processed_answers': processed_answers,
            'recommendations': cls._generate_recommendations(skill_level, topic_analysis, difficulty_performance)
        }
        
        # Save analysis results to file system
        cls._save_survey_answers(user_id, subject, analysis_results)
        
        # Store skill level in database
        try:
            SurveyResultService.create_survey_result(user_id, subject, skill_level)
            logger.info(f"Stored survey result in database: {user_id} - {subject} - {skill_level}")
        except Exception as e:
            logger.error(f"Failed to store survey result in database: {str(e)}")
            # Don't fail the entire process if database storage fails
        
        logger.info(f"Survey analysis completed for {user_id}, skill level: {skill_level}")
        return analysis_results
    
    @classmethod
    def get_survey_results(cls, user_id: str, subject: str) -> Dict[str, Any]:
        """
        Retrieve survey analysis results for a user and subject
        
        Args:
            user_id: The user ID
            subject: The subject
            
        Returns:
            Dictionary containing analysis results or None if not found
        """
        try:
            file_path = f"users/{user_id}/{subject}/survey_answers.json"
            results = FileService.load_json(file_path)
            logger.info(f"Retrieved survey results for {user_id} - {subject}")
            return results
        except FileNotFoundError:
            logger.info(f"No survey results found for {user_id} - {subject}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving survey results for {user_id} - {subject}: {str(e)}")
            raise
    
    @classmethod
    def _load_survey(cls, user_id: str, subject: str) -> Dict[str, Any]:
        """Load the original survey from file system"""
        try:
            file_path = f"users/{user_id}/{subject}/survey.json"
            return FileService.load_json(file_path)
        except Exception as e:
            logger.error(f"Failed to load survey for {user_id} - {subject}: {str(e)}")
            return None
    
    @classmethod
    def _validate_answers(cls, answers: List[Dict[str, Any]], survey: Dict[str, Any]) -> None:
        """Validate that answers have correct format and match survey questions"""
        if not isinstance(answers, list):
            raise ValueError("Answers must be a list")
        
        if len(answers) == 0:
            raise ValueError("Answers list cannot be empty")
        
        survey_question_ids = {q['id'] for q in survey['questions']}
        
        for answer in answers:
            if not isinstance(answer, dict):
                raise ValueError("Each answer must be a dictionary")
            
            if 'question_id' not in answer:
                raise ValueError("Each answer must have a question_id")
            
            if 'answer' not in answer:
                raise ValueError("Each answer must have an answer field")
            
            question_id = answer['question_id']
            if question_id not in survey_question_ids:
                raise ValueError(f"Question ID {question_id} not found in survey")
            
            # Validate answer is within valid range (0-3 for multiple choice)
            user_answer = answer['answer']
            if not isinstance(user_answer, int) or user_answer < 0 or user_answer > 3:
                raise ValueError(f"Answer for question {question_id} must be an integer between 0 and 3")
    
    @classmethod
    def _determine_skill_level(cls, weighted_accuracy: float, difficulty_performance: Dict[str, Dict[str, int]]) -> str:
        """
        Determine skill level based on weighted accuracy and difficulty performance
        
        Args:
            weighted_accuracy: Overall weighted accuracy score
            difficulty_performance: Performance breakdown by difficulty
            
        Returns:
            Skill level string ('beginner', 'intermediate', 'advanced')
        """
        # Base determination on weighted accuracy
        if weighted_accuracy >= cls.SKILL_LEVEL_THRESHOLDS['advanced']:
            base_level = 'advanced'
        elif weighted_accuracy >= cls.SKILL_LEVEL_THRESHOLDS['intermediate']:
            base_level = 'intermediate'
        else:
            base_level = 'beginner'
        
        # Adjust based on performance in advanced questions
        advanced_perf = difficulty_performance['advanced']
        if advanced_perf['total'] > 0:
            advanced_accuracy = advanced_perf['correct'] / advanced_perf['total']
            
            # If user performs well on advanced questions, upgrade level
            if advanced_accuracy >= 0.7 and base_level == 'intermediate':
                return 'advanced'
            
            # If user performs poorly on advanced questions, consider downgrade
            if advanced_accuracy < 0.3 and base_level == 'advanced':
                return 'intermediate'
        
        # Check beginner performance for potential downgrade
        beginner_perf = difficulty_performance['beginner']
        if beginner_perf['total'] > 0:
            beginner_accuracy = beginner_perf['correct'] / beginner_perf['total']
            
            # If user struggles with beginner questions, ensure they're marked as beginner
            if beginner_accuracy < 0.5 and base_level != 'beginner':
                return 'beginner'
        
        return base_level
    
    @classmethod
    def _analyze_topic_performance(cls, topic_performance: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Analyze performance by topic to identify strengths and weaknesses"""
        topic_analysis = {
            'strengths': [],
            'weaknesses': [],
            'topic_scores': {}
        }
        
        for topic, performance in topic_performance.items():
            if performance['total'] == 0:
                continue
            
            accuracy = performance['correct'] / performance['total']
            topic_analysis['topic_scores'][topic] = {
                'accuracy': accuracy,
                'correct': performance['correct'],
                'total': performance['total']
            }
            
            # Classify as strength or weakness
            if accuracy >= 0.8:
                topic_analysis['strengths'].append(topic)
            elif accuracy < 0.5:
                topic_analysis['weaknesses'].append(topic)
        
        return topic_analysis
    
    @classmethod
    def _generate_recommendations(cls, skill_level: str, topic_analysis: Dict[str, Any], 
                                difficulty_performance: Dict[str, Dict[str, int]]) -> List[str]:
        """Generate learning recommendations based on analysis"""
        recommendations = []
        
        # Skill level based recommendations
        if skill_level == 'beginner':
            recommendations.append("Focus on fundamental concepts and basic syntax")
            recommendations.append("Practice with simple exercises and examples")
        elif skill_level == 'intermediate':
            recommendations.append("Work on more complex problems and design patterns")
            recommendations.append("Explore advanced features and best practices")
        else:  # advanced
            recommendations.append("Challenge yourself with complex projects")
            recommendations.append("Consider contributing to open source or mentoring others")
        
        # Topic-specific recommendations
        if topic_analysis['weaknesses']:
            weak_topics = ', '.join(topic_analysis['weaknesses'])
            recommendations.append(f"Review and practice: {weak_topics}")
        
        if topic_analysis['strengths']:
            strong_topics = ', '.join(topic_analysis['strengths'])
            recommendations.append(f"Build on your strengths in: {strong_topics}")
        
        # Difficulty-specific recommendations
        for difficulty, perf in difficulty_performance.items():
            if perf['total'] > 0:
                accuracy = perf['correct'] / perf['total']
                if accuracy < 0.5:
                    recommendations.append(f"Spend more time on {difficulty}-level concepts")
        
        return recommendations
    
    @classmethod
    def _save_survey_answers(cls, user_id: str, subject: str, analysis_results: Dict[str, Any]) -> None:
        """Save survey analysis results to file system"""
        try:
            file_path = f"users/{user_id}/{subject}/survey_answers.json"
            FileService.save_json(file_path, analysis_results)
            logger.info(f"Saved survey analysis results to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save survey analysis results: {str(e)}")
            raise
    
    @classmethod
    def validate_analysis_results(cls, results: Dict[str, Any]) -> bool:
        """
        Validate that analysis results have the correct structure
        
        Args:
            results: Analysis results dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'user_id', 'subject', 'processed_at', 'total_questions',
            'correct_answers', 'accuracy', 'skill_level', 'topic_analysis',
            'processed_answers', 'recommendations'
        ]
        
        # Check required top-level fields
        for field in required_fields:
            if field not in results:
                logger.error(f"Analysis results missing required field: {field}")
                return False
        
        # Validate skill level
        if results['skill_level'] not in ['beginner', 'intermediate', 'advanced']:
            logger.error(f"Invalid skill level: {results['skill_level']}")
            return False
        
        # Validate accuracy is between 0 and 1
        if not (0 <= results['accuracy'] <= 1):
            logger.error(f"Invalid accuracy value: {results['accuracy']}")
            return False
        
        # Validate processed answers structure
        if not isinstance(results['processed_answers'], list):
            logger.error("Processed answers must be a list")
            return False
        
        for answer in results['processed_answers']:
            required_answer_fields = ['question_id', 'user_answer', 'correct_answer', 'is_correct']
            for field in required_answer_fields:
                if field not in answer:
                    logger.error(f"Processed answer missing required field: {field}")
                    return False
        
        return True