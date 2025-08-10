"""
Unit tests for Lesson Planning Chain
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.langchain_chains import LessonPlannerChain

class TestLessonPlannerChain:
    """Test lesson planning functionality"""
    
    @pytest.fixture
    def sample_curriculum_data(self):
        """Sample curriculum data for testing"""
        return {
            "curriculum": {
                "subject": "python",
                "skill_level": "intermediate",
                "total_lessons": 3,
                "learning_objectives": [
                    "Master Python fundamentals",
                    "Build practical applications",
                    "Understand best practices"
                ],
                "topics": [
                    {
                        "lesson_id": 1,
                        "title": "Advanced Variables and Data Types",
                        "topics": ["dictionaries", "sets", "type_hints"],
                        "prerequisites": [],
                        "difficulty": "intermediate",
                        "estimated_duration": "45-60 minutes"
                    },
                    {
                        "lesson_id": 2,
                        "title": "Object-Oriented Programming",
                        "topics": ["classes", "inheritance", "polymorphism"],
                        "prerequisites": ["variables"],
                        "difficulty": "intermediate",
                        "estimated_duration": "45-60 minutes"
                    },
                    {
                        "lesson_id": 3,
                        "title": "File Handling and I/O",
                        "topics": ["file_operations", "csv_processing", "error_handling"],
                        "prerequisites": ["classes"],
                        "difficulty": "intermediate",
                        "estimated_duration": "45-60 minutes"
                    }
                ]
            },
            "generated_at": "2024-01-15T10:00:00Z",
            "generation_stage": "curriculum_complete"
        }
    
    @pytest.fixture
    def sample_rag_docs(self):
        """Sample RAG documents for testing"""
        return [
            "Create detailed lesson plans with clear time allocations",
            "Include specific learning objectives for each lesson",
            "Provide variety in activities and assessment methods"
        ]
    
    @pytest.fixture
    def expected_lesson_plans_output(self):
        """Expected lesson plans output structure"""
        return {
            "lesson_plans": [
                {
                    "lesson_id": 1,
                    "title": "Advanced Variables and Data Types",
                    "learning_objectives": [
                        "Understand and use Python dictionaries effectively",
                        "Work with sets for unique data collections",
                        "Apply type hints for better code documentation"
                    ],
                    "structure": {
                        "introduction": "5 minutes",
                        "main_content": "25 minutes",
                        "examples": "15 minutes",
                        "exercises": "15 minutes",
                        "summary": "5 minutes"
                    },
                    "activities": [
                        "Interactive demonstration of dictionary operations",
                        "Guided practice with set operations",
                        "Type hints implementation exercise"
                    ],
                    "assessment": "Coding exercises with dictionaries and sets",
                    "materials_needed": [
                        "Python IDE",
                        "Code examples"
                    ],
                    "key_concepts": [
                        "dictionaries",
                        "sets", 
                        "type_hints"
                    ]
                },
                {
                    "lesson_id": 2,
                    "title": "Object-Oriented Programming",
                    "learning_objectives": [
                        "Create and use Python classes",
                        "Implement inheritance relationships",
                        "Understand polymorphism concepts"
                    ],
                    "structure": {
                        "introduction": "5 minutes",
                        "main_content": "25 minutes",
                        "examples": "15 minutes",
                        "exercises": "15 minutes",
                        "summary": "5 minutes"
                    },
                    "activities": [
                        "Class creation demonstration",
                        "Inheritance examples",
                        "Polymorphism coding challenge"
                    ],
                    "assessment": "Build a class hierarchy project",
                    "materials_needed": [
                        "Python IDE",
                        "OOP examples"
                    ],
                    "key_concepts": [
                        "classes",
                        "inheritance",
                        "polymorphism"
                    ]
                }
            ],
            "generated_at": "2024-01-15T10:00:00Z",
            "generation_stage": "lesson_plans_complete"
        }
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_lesson_plans_generation_success(self, mock_llm_class, mock_validate, 
                                           sample_curriculum_data, sample_rag_docs, 
                                           expected_lesson_plans_output):
        """Test successful lesson plans generation"""
        mock_validate.return_value = True
        
        # Mock the LLM chain
        mock_chain = Mock()
        mock_chain.run.return_value = expected_lesson_plans_output
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            lesson_planner = LessonPlannerChain()
            result = lesson_planner.generate_lesson_plans(
                sample_curriculum_data, 
                "python", 
                sample_rag_docs
            )
        
        assert "lesson_plans" in result
        lesson_plans = result["lesson_plans"]
        assert len(lesson_plans) == 2
        
        # Check first lesson plan structure
        first_plan = lesson_plans[0]
        assert first_plan["lesson_id"] == 1
        assert first_plan["title"] == "Advanced Variables and Data Types"
        assert len(first_plan["learning_objectives"]) >= 2
        assert "structure" in first_plan
        assert "activities" in first_plan
        assert "assessment" in first_plan
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_format_curriculum_data(self, mock_llm_class, mock_validate, sample_curriculum_data):
        """Test formatting of curriculum data for prompt"""
        mock_validate.return_value = True
        
        lesson_planner = LessonPlannerChain()
        formatted_data = lesson_planner._format_curriculum_data(sample_curriculum_data)
        
        assert "Subject: python" in formatted_data
        assert "Skill Level: intermediate" in formatted_data
        assert "Total Lessons: 3" in formatted_data
        assert "Master Python fundamentals" in formatted_data
        assert "Lesson 1: Advanced Variables and Data Types" in formatted_data
        assert "Topics: dictionaries, sets, type_hints" in formatted_data
        assert "Difficulty: intermediate" in formatted_data
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_lesson_plans_validation_missing_structure(self, mock_llm_class, mock_validate, 
                                                     sample_curriculum_data, sample_rag_docs):
        """Test lesson plans generation with invalid output structure"""
        mock_validate.return_value = True
        
        # Mock invalid output (missing lesson_plans key)
        invalid_output = {
            "invalid_key": "invalid_value"
        }
        
        mock_chain = Mock()
        mock_chain.run.return_value = invalid_output
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            lesson_planner = LessonPlannerChain()
            
            with pytest.raises(ValueError, match="do not have required structure"):
                lesson_planner.generate_lesson_plans(
                    sample_curriculum_data, 
                    "python", 
                    sample_rag_docs
                )
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_lesson_plans_validation_empty_plans(self, mock_llm_class, mock_validate, 
                                                sample_curriculum_data, sample_rag_docs):
        """Test lesson plans generation with empty lesson plans"""
        mock_validate.return_value = True
        
        # Mock output with empty lesson plans
        invalid_output = {
            "lesson_plans": []
        }
        
        mock_chain = Mock()
        mock_chain.run.return_value = invalid_output
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            lesson_planner = LessonPlannerChain()
            
            with pytest.raises(ValueError, match="No lesson plans generated"):
                lesson_planner.generate_lesson_plans(
                    sample_curriculum_data, 
                    "python", 
                    sample_rag_docs
                )
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_lesson_plans_validation_invalid_plan_structure(self, mock_llm_class, mock_validate, 
                                                          sample_curriculum_data, sample_rag_docs):
        """Test lesson plans generation with invalid individual lesson plan structure"""
        mock_validate.return_value = True
        
        # Mock output with invalid lesson plan structure
        invalid_output = {
            "lesson_plans": [
                {
                    "lesson_id": 1,
                    "title": "Test Lesson"
                    # Missing required keys: learning_objectives, structure, activities, assessment
                }
            ]
        }
        
        mock_chain = Mock()
        mock_chain.run.return_value = invalid_output
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            lesson_planner = LessonPlannerChain()
            
            with pytest.raises(ValueError, match="Lesson plan 1 has invalid structure"):
                lesson_planner.generate_lesson_plans(
                    sample_curriculum_data, 
                    "python", 
                    sample_rag_docs
                )
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_curriculum_data_without_topics(self, mock_llm_class, mock_validate, sample_rag_docs):
        """Test lesson plans generation with curriculum data missing topics"""
        mock_validate.return_value = True
        
        invalid_curriculum_data = {
            "curriculum": {
                "subject": "python",
                "skill_level": "intermediate",
                "total_lessons": 0,
                "learning_objectives": [],
                "topics": []  # Empty topics
            }
        }
        
        lesson_planner = LessonPlannerChain()
        
        with pytest.raises(ValueError, match="No topics found in curriculum data"):
            lesson_planner.generate_lesson_plans(
                invalid_curriculum_data, 
                "python", 
                sample_rag_docs
            )
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_prompt_template_structure(self, mock_llm_class, mock_validate):
        """Test that prompt template has correct input variables"""
        mock_validate.return_value = True
        
        lesson_planner = LessonPlannerChain()
        prompt_template = lesson_planner.get_prompt_template()
        
        expected_variables = ["curriculum_data", "subject", "skill_level", "rag_guidelines"]
        assert set(prompt_template.input_variables) == set(expected_variables)
        
        # Check that template contains key instructions
        template_text = prompt_template.template
        assert "detailed lesson plans" in template_text
        assert "60 minutes" in template_text
        assert "JSON object" in template_text
        assert "lesson_plans" in template_text
        assert "learning_objectives" in template_text
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_lesson_plans_generation_without_rag_docs(self, mock_llm_class, mock_validate, 
                                                    sample_curriculum_data, expected_lesson_plans_output):
        """Test lesson plans generation without RAG documents"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = expected_lesson_plans_output
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            lesson_planner = LessonPlannerChain()
            result = lesson_planner.generate_lesson_plans(
                sample_curriculum_data, 
                "python", 
                None  # No RAG docs
            )
        
        # Should still work with default guidelines
        assert "lesson_plans" in result
        assert len(result["lesson_plans"]) == 2
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_different_skill_levels(self, mock_llm_class, mock_validate, 
                                  sample_rag_docs, expected_lesson_plans_output):
        """Test lesson plans generation for different skill levels"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = expected_lesson_plans_output
        
        skill_levels = ['beginner', 'intermediate', 'advanced']
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            lesson_planner = LessonPlannerChain()
            
            for skill_level in skill_levels:
                curriculum_data = {
                    "curriculum": {
                        "subject": "python",
                        "skill_level": skill_level,
                        "total_lessons": 2,
                        "learning_objectives": ["Test objective"],
                        "topics": [
                            {
                                "lesson_id": 1,
                                "title": "Test Lesson",
                                "topics": ["test_topic"],
                                "prerequisites": [],
                                "difficulty": skill_level,
                                "estimated_duration": "60 minutes"
                            }
                        ]
                    }
                }
                
                result = lesson_planner.generate_lesson_plans(
                    curriculum_data, 
                    "python", 
                    sample_rag_docs
                )
                
                assert "lesson_plans" in result
                assert len(result["lesson_plans"]) >= 1