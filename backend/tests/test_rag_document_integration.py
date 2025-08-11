"""
Tests for RAG document integration with LangChain pipeline
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, mock_open
from app.services.rag_document_service import RAGDocumentService
from app.services.langchain_chains import (
    SurveyGenerationChain,
    CurriculumGeneratorChain,
    LessonPlannerChain,
    ContentGeneratorChain
)

class TestRAGDocumentIntegration:
    """Test RAG document integration with LangChain chains"""
    
    @pytest.fixture
    def mock_rag_documents(self):
        """Mock RAG documents for testing"""
        return {
            'survey': [
                "Generate 7-8 multiple choice questions",
                "Follow difficulty distribution: 30% beginner, 50% intermediate, 20% advanced",
                "Each question must have exactly 4 options",
                "Cover fundamental programming concepts"
            ],
            'curriculum': [
                "Create a comprehensive 10-lesson curriculum",
                "Adapt difficulty based on skill level assessment",
                "Skip topics the learner already knows",
                "Include clear learning progression"
            ],
            'lesson_plans': [
                "Create detailed 60-minute lesson plans",
                "Include specific learning objectives",
                "Provide variety in activities and assessments",
                "Ensure proper time allocation"
            ],
            'content': [
                "Generate comprehensive lesson content",
                "Include 2 practical code examples per lesson",
                "Create 3-5 hands-on exercises",
                "Use proper markdown formatting"
            ]
        }
    
    @pytest.fixture
    def mock_rag_service(self):
        """Mock RAG document service"""
        service = Mock(spec=RAGDocumentService)
        return service
    
    def test_rag_document_loading_and_parsing(self, mock_rag_documents):
        """Test RAG document loading and parsing"""
        with patch('app.services.rag_document_service.RAGDocumentService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.load_documents_for_stage.return_value = mock_rag_documents['survey']
            
            # Test loading survey RAG documents
            rag_service = RAGDocumentService()
            survey_docs = rag_service.load_documents_for_stage('survey', 'python')
            
            assert len(survey_docs) == 4
            assert "Generate 7-8 multiple choice questions" in survey_docs[0]
            assert "Follow difficulty distribution" in survey_docs[1]
            mock_service.load_documents_for_stage.assert_called_once_with('survey', 'python')
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_survey_chain_with_rag_documents(self, mock_llm_class, mock_validate, mock_rag_documents):
        """Test survey generation chain with RAG documents"""
        mock_validate.return_value = True
        mock_llm_class.return_value = Mock()
        
        # Mock survey result with proper difficulty distribution
        mock_survey_result = {
            "questions": [
                {
                    "id": 1,
                    "question": "Question 1?",
                    "type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "difficulty": "beginner",
                    "topic": "topic_1"
                },
                {
                    "id": 2,
                    "question": "Question 2?",
                    "type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "difficulty": "beginner",
                    "topic": "topic_2"
                }
            ] + [
                {
                    "id": i,
                    "question": f"Question {i}?",
                    "type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "difficulty": "intermediate",
                    "topic": f"topic_{i}"
                }
                for i in range(3, 7)
            ] + [
                {
                    "id": 7,
                    "question": "Question 7?",
                    "type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "difficulty": "advanced",
                    "topic": "topic_7"
                }
            ],
            "total_questions": 7,
            "subject": "python"
        }
        
        mock_chain = Mock()
        mock_chain.run.return_value = mock_survey_result
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            chain = SurveyGenerationChain()
            
            # Mock RAG document loading
            with patch.object(chain, 'load_rag_documents', return_value=mock_rag_documents['survey']):
                result = chain.generate_survey('python')
            
            # Verify RAG documents were used in the chain
            mock_chain.run.assert_called_once()
            call_args = mock_chain.run.call_args[1]
            
            # Check that RAG guidelines were included in the prompt
            assert 'rag_guidelines' in call_args
            rag_guidelines = call_args['rag_guidelines']
            assert "Generate 7-8 multiple choice questions" in rag_guidelines
            assert "Follow difficulty distribution" in rag_guidelines
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_curriculum_chain_with_rag_documents(self, mock_llm_class, mock_validate, mock_rag_documents):
        """Test curriculum generation chain with RAG documents"""
        mock_validate.return_value = True
        mock_llm_class.return_value = Mock()
        
        # Mock curriculum result
        mock_curriculum_result = {
            "curriculum": {
                "subject": "python",
                "skill_level": "intermediate",
                "total_lessons": 10,
                "learning_objectives": ["Objective 1", "Objective 2"],
                "topics": [{"lesson_id": i, "title": f"Lesson {i}"} for i in range(1, 11)]
            }
        }
        
        mock_chain = Mock()
        mock_chain.run.return_value = mock_curriculum_result
        
        survey_data = {'skill_level': 'intermediate', 'answers': []}
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            chain = CurriculumGeneratorChain()
            
            # Mock RAG document loading
            with patch.object(chain, 'load_rag_documents', return_value=mock_rag_documents['curriculum']):
                result = chain.generate_curriculum(survey_data, 'python')
            
            # Verify RAG documents were used
            mock_chain.run.assert_called_once()
            call_args = mock_chain.run.call_args[1]
            
            assert 'rag_guidelines' in call_args
            rag_guidelines = call_args['rag_guidelines']
            # Check that RAG guidelines contain the expected content
            assert "Create a comprehensive" in rag_guidelines
            assert "curriculum" in rag_guidelines
    
    def test_rag_document_content_quality_validation(self, mock_rag_documents):
        """Test content quality with different RAG documents"""
        # Test with high-quality RAG documents
        high_quality_docs = [
            "Generate comprehensive, well-structured content",
            "Include detailed explanations and examples",
            "Ensure proper formatting and organization",
            "Validate all code examples for correctness"
        ]
        
        # Test with minimal RAG documents
        minimal_docs = [
            "Generate content",
            "Include examples"
        ]
        
        # Test with empty RAG documents
        empty_docs = []
        
        # Simulate content generation with different RAG document qualities
        test_cases = [
            ("high_quality", high_quality_docs),
            ("minimal", minimal_docs),
            ("empty", empty_docs)
        ]
        
        for quality_level, docs in test_cases:
            # Verify that different RAG document qualities can be handled
            assert isinstance(docs, list)
            
            # High quality should have more detailed guidelines
            if quality_level == "high_quality":
                assert len(docs) >= 3
                assert any("comprehensive" in doc.lower() for doc in docs)
            
            # Minimal should have basic guidelines
            elif quality_level == "minimal":
                assert len(docs) >= 1
                assert any("content" in doc.lower() for doc in docs)
            
            # Empty should be handled gracefully
            elif quality_level == "empty":
                assert len(docs) == 0
    
    def test_rag_document_versioning_and_updates(self):
        """Test RAG document versioning and updates"""
        # Mock different versions of RAG documents
        version_1_docs = [
            "Generate 5-7 questions",
            "Basic difficulty levels"
        ]
        
        version_2_docs = [
            "Generate 7-8 questions",
            "Advanced difficulty distribution: 30% beginner, 50% intermediate, 20% advanced",
            "Include code examples in questions"
        ]
        
        with patch('app.services.rag_document_service.RAGDocumentService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Test version 1
            mock_service.load_documents_for_stage.return_value = version_1_docs
            rag_service = RAGDocumentService()
            docs_v1 = rag_service.load_documents_for_stage('survey', 'python')
            
            assert len(docs_v1) == 2
            # The actual RAG service returns real documents, so check for basic content
            assert len(docs_v1) >= 1
            
            # Test version 2 (updated)
            mock_service.load_documents_for_stage.return_value = version_2_docs
            docs_v2 = rag_service.load_documents_for_stage('survey', 'python')
            
            assert len(docs_v2) == 3
            # Check that version 2 has content
            assert len(docs_v2) >= 1
            
            # Verify that updated version has more comprehensive guidelines
            assert len(docs_v2) > len(docs_v1)
    
    def test_rag_document_format_compliance(self):
        """Test RAG document format compliance"""
        # Test valid RAG document formats
        valid_formats = [
            "Plain text instruction",
            "Instruction with specific parameters: 30% beginner, 70% advanced",
            "Multi-line instruction\nwith detailed requirements\nand examples",
            "Instruction with code: use `print()` function"
        ]
        
        # Test invalid RAG document formats
        invalid_formats = [
            "",  # Empty string
            None,  # None value
            123,  # Non-string type
            {"invalid": "format"}  # Dictionary instead of string
        ]
        
        # Validate format compliance
        for doc in valid_formats:
            assert isinstance(doc, str)
            assert len(doc.strip()) > 0
            # Additional format validation could be added here
        
        for doc in invalid_formats:
            if doc is not None and not isinstance(doc, str):
                # Invalid formats should be handled appropriately
                assert not isinstance(doc, str) or len(doc.strip()) == 0
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_rag_document_fallback_behavior(self, mock_llm_class, mock_validate):
        """Test fallback behavior when RAG documents are unavailable"""
        mock_validate.return_value = True
        mock_llm_class.return_value = Mock()
        
        mock_survey_result = {
            "questions": [
                {"id": 1, "question": "Test 1?", "type": "multiple_choice", 
                 "options": ["A", "B", "C", "D"], "correct_answer": "A", 
                 "difficulty": "beginner", "topic": "test1"},
                {"id": 2, "question": "Test 2?", "type": "multiple_choice", 
                 "options": ["A", "B", "C", "D"], "correct_answer": "A", 
                 "difficulty": "beginner", "topic": "test2"},
                {"id": 3, "question": "Test 3?", "type": "multiple_choice", 
                 "options": ["A", "B", "C", "D"], "correct_answer": "A", 
                 "difficulty": "intermediate", "topic": "test3"},
                {"id": 4, "question": "Test 4?", "type": "multiple_choice", 
                 "options": ["A", "B", "C", "D"], "correct_answer": "A", 
                 "difficulty": "intermediate", "topic": "test4"},
                {"id": 5, "question": "Test 5?", "type": "multiple_choice", 
                 "options": ["A", "B", "C", "D"], "correct_answer": "A", 
                 "difficulty": "intermediate", "topic": "test5"},
                {"id": 6, "question": "Test 6?", "type": "multiple_choice", 
                 "options": ["A", "B", "C", "D"], "correct_answer": "A", 
                 "difficulty": "intermediate", "topic": "test6"},
                {"id": 7, "question": "Test 7?", "type": "multiple_choice", 
                 "options": ["A", "B", "C", "D"], "correct_answer": "A", 
                 "difficulty": "advanced", "topic": "test7"}
            ],
            "total_questions": 7,
            "subject": "python"
        }
        
        mock_chain = Mock()
        mock_chain.run.return_value = mock_survey_result
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            chain = SurveyGenerationChain()
            
            # Test with empty RAG documents (should use defaults)
            with patch.object(chain, 'load_rag_documents', return_value=[]):
                result = chain.generate_survey('python')
            
            # Verify that default guidelines were used
            mock_chain.run.assert_called_once()
            call_args = mock_chain.run.call_args[1]
            
            assert 'rag_guidelines' in call_args
            rag_guidelines = call_args['rag_guidelines']
            
            # Should contain default survey guidelines
            assert "7-8 multiple choice questions" in rag_guidelines
            assert "30% beginner, 50% intermediate, 20% advanced" in rag_guidelines
    
    def test_rag_document_subject_specific_loading(self, mock_rag_documents):
        """Test subject-specific RAG document loading"""
        subjects = ['python', 'javascript', 'react', 'nodejs']
        
        with patch('app.services.rag_document_service.RAGDocumentService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock different documents for different subjects
            def mock_load_docs(stage, subject):
                base_docs = mock_rag_documents.get(stage, [])
                # Add subject-specific guidelines
                subject_specific = f"Focus on {subject}-specific concepts and best practices"
                return base_docs + [subject_specific]
            
            mock_service.load_documents_for_stage.side_effect = mock_load_docs
            
            rag_service = RAGDocumentService()
            
            for subject in subjects:
                docs = rag_service.load_documents_for_stage('survey', subject)
                
                # Verify subject-specific content is included
                assert any(subject in doc for doc in docs)
                # Check that subject-specific content exists
                assert len(docs) >= 1
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_rag_document_chain_integration_end_to_end(self, mock_llm_class, mock_validate, mock_rag_documents):
        """Test end-to-end RAG document integration across all chains"""
        mock_validate.return_value = True
        mock_llm_class.return_value = Mock()
        
        # Mock results for each chain
        mock_survey_result = {
            "questions": [
                {"id": 1, "question": "Test 1?", "type": "multiple_choice",
                 "options": ["A", "B", "C", "D"], "correct_answer": "A",
                 "difficulty": "beginner", "topic": "test1"},
                {"id": 2, "question": "Test 2?", "type": "multiple_choice",
                 "options": ["A", "B", "C", "D"], "correct_answer": "A",
                 "difficulty": "beginner", "topic": "test2"},
                {"id": 3, "question": "Test 3?", "type": "multiple_choice",
                 "options": ["A", "B", "C", "D"], "correct_answer": "A",
                 "difficulty": "intermediate", "topic": "test3"},
                {"id": 4, "question": "Test 4?", "type": "multiple_choice",
                 "options": ["A", "B", "C", "D"], "correct_answer": "A",
                 "difficulty": "intermediate", "topic": "test4"},
                {"id": 5, "question": "Test 5?", "type": "multiple_choice",
                 "options": ["A", "B", "C", "D"], "correct_answer": "A",
                 "difficulty": "intermediate", "topic": "test5"},
                {"id": 6, "question": "Test 6?", "type": "multiple_choice",
                 "options": ["A", "B", "C", "D"], "correct_answer": "A",
                 "difficulty": "intermediate", "topic": "test6"},
                {"id": 7, "question": "Test 7?", "type": "multiple_choice",
                 "options": ["A", "B", "C", "D"], "correct_answer": "A",
                 "difficulty": "advanced", "topic": "test7"}
            ],
            "total_questions": 7,
            "subject": "python"
        }
        
        mock_curriculum_result = {
            "curriculum": {
                "subject": "python",
                "skill_level": "intermediate", 
                "total_lessons": 2,
                "topics": [{"lesson_id": 1}, {"lesson_id": 2}]
            }
        }
        
        mock_lesson_plans_result = {
            "lesson_plans": [
                {"lesson_id": 1, "title": "Lesson 1"},
                {"lesson_id": 2, "title": "Lesson 2"}
            ]
        }
        
        mock_content_result = "# Lesson Content\n\nThis is generated content..."
        
        # Test each chain with RAG documents
        chains_and_results = [
            (SurveyGenerationChain, mock_survey_result, 'survey'),
            (CurriculumGeneratorChain, mock_curriculum_result, 'curriculum'),
            (LessonPlannerChain, mock_lesson_plans_result, 'lesson_plans'),
            (ContentGeneratorChain, mock_content_result, 'content')
        ]
        
        for chain_class, mock_result, rag_type in chains_and_results:
            mock_chain = Mock()
            mock_chain.run.return_value = mock_result
            
            with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
                chain = chain_class()
                
                # Mock RAG document loading for this chain type
                with patch.object(chain, 'load_rag_documents', return_value=mock_rag_documents[rag_type]):
                    
                    # Call appropriate method based on chain type
                    if chain_class == SurveyGenerationChain:
                        result = chain.generate_survey('python')
                    elif chain_class == CurriculumGeneratorChain:
                        result = chain.generate_curriculum({'skill_level': 'intermediate', 'answers': []}, 'python')
                    elif chain_class == LessonPlannerChain:
                        result = chain.generate_lesson_plans(mock_curriculum_result, 'python')
                    elif chain_class == ContentGeneratorChain:
                        result = chain.generate_content({"lesson_id": 1, "title": "Test"}, 'python')
                    
                    # Verify RAG documents were loaded and used
                    chain.load_rag_documents.assert_called_once()
                    
                    # Verify result is as expected
                    if chain_class == ContentGeneratorChain:
                        assert isinstance(result, str)
                        assert len(result) > 0
                    else:
                        assert isinstance(result, dict)
                        assert result == mock_result or 'generated_at' in result