"""
Unit tests for RAG Document Service
"""
import pytest
import tempfile
import os
from pathlib import Path
from app.services.rag_document_service import RAGDocumentService

class TestRAGDocumentService:
    """Test RAG Document Service functionality"""
    
    @pytest.fixture
    def temp_rag_dir(self):
        """Create a temporary directory with test RAG documents"""
        with tempfile.TemporaryDirectory() as temp_dir:
            rag_path = Path(temp_dir) / "rag_docs"
            rag_path.mkdir()
            
            # Create test documents
            (rag_path / "content_guidelines.md").write_text(
                "# Content Guidelines\n\n## Lesson Structure Template\n\n```python\ncode example\n```"
            )
            
            (rag_path / "survey_guidelines.md").write_text(
                "# Survey Guidelines\n\n## Question Format\n\nmultiple_choice\nbeginner\nintermediate\nadvanced"
            )
            
            # Create subjects directory
            subjects_path = rag_path / "subjects"
            subjects_path.mkdir()
            
            (subjects_path / "python_templates.md").write_text(
                "# Python Templates\n\n## Python-specific content"
            )
            
            yield str(rag_path)
    
    def test_service_initialization(self, temp_rag_dir):
        """Test RAG service initialization"""
        service = RAGDocumentService(temp_rag_dir)
        
        assert service.rag_docs_path == Path(temp_rag_dir)
        assert service._document_cache == {}
    
    def test_load_general_document(self, temp_rag_dir):
        """Test loading general RAG documents"""
        service = RAGDocumentService(temp_rag_dir)
        
        content = service.load_document("content_guidelines")
        
        assert "Content Guidelines" in content
        assert "Lesson Structure Template" in content
        assert "code example" in content
    
    def test_load_subject_specific_document(self, temp_rag_dir):
        """Test loading subject-specific RAG documents"""
        service = RAGDocumentService(temp_rag_dir)
        
        content = service.load_document("templates", "python")
        
        assert "Python Templates" in content
        assert "Python-specific content" in content
    
    def test_load_nonexistent_document(self, temp_rag_dir):
        """Test loading non-existent document returns empty string"""
        service = RAGDocumentService(temp_rag_dir)
        
        content = service.load_document("nonexistent")
        
        assert content == ""
    
    def test_document_caching(self, temp_rag_dir):
        """Test that documents are cached after first load"""
        service = RAGDocumentService(temp_rag_dir)
        
        # First load
        content1 = service.load_document("content_guidelines")
        assert len(service._document_cache) == 1
        
        # Second load should use cache
        content2 = service.load_document("content_guidelines")
        assert content1 == content2
        assert len(service._document_cache) == 1
    
    def test_load_documents_for_stage(self, temp_rag_dir):
        """Test loading documents for specific pipeline stages"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Test survey stage
        survey_docs = service.load_documents_for_stage("survey")
        assert len(survey_docs) == 1
        assert "Survey Guidelines" in survey_docs[0]
        
        # Test content stage with subject
        content_docs = service.load_documents_for_stage("content", "python")
        assert len(content_docs) == 2  # content_guidelines + python_templates
        assert any("Content Guidelines" in doc for doc in content_docs)
        assert any("Python Templates" in doc for doc in content_docs)
    
    def test_get_available_documents(self, temp_rag_dir):
        """Test getting list of available documents"""
        service = RAGDocumentService(temp_rag_dir)
        
        available = service.get_available_documents()
        
        assert "general" in available
        assert "subjects" in available
        assert "content_guidelines" in available["general"]
        assert "survey_guidelines" in available["general"]
        assert "python" in available["subjects"]
    
    def test_validate_document_structure(self, temp_rag_dir):
        """Test document structure validation"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Load and validate content guidelines
        content = service.load_document("content_guidelines")
        validation = service.validate_document_structure("content_guidelines", content)
        
        assert validation["has_content"] is True
        assert validation["has_headers"] is True
        assert validation["has_examples"] is True
        assert validation["has_lesson_structure"] is True
        assert validation["has_exercise_format"] is False  # Not in test content
    
    def test_validate_survey_guidelines(self, temp_rag_dir):
        """Test survey guidelines validation"""
        service = RAGDocumentService(temp_rag_dir)
        
        content = service.load_document("survey_guidelines")
        validation = service.validate_document_structure("survey_guidelines", content)
        
        assert validation["has_content"] is True
        assert validation["has_question_format"] is True
        assert validation["has_difficulty_levels"] is True
    
    def test_clear_cache(self, temp_rag_dir):
        """Test clearing document cache"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Load a document to populate cache
        service.load_document("content_guidelines")
        assert len(service._document_cache) == 1
        
        # Clear cache
        service.clear_cache()
        assert len(service._document_cache) == 0
    
    def test_reload_document(self, temp_rag_dir):
        """Test reloading document from disk"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Load document initially
        content1 = service.load_document("content_guidelines")
        
        # Modify the file
        doc_path = Path(temp_rag_dir) / "content_guidelines.md"
        doc_path.write_text("# Modified Content")
        
        # Reload should get new content
        content2 = service.reload_document("content_guidelines")
        assert content2 == "# Modified Content"
        assert content1 != content2
    
    def test_get_document_stats(self, temp_rag_dir):
        """Test getting document statistics"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Load some documents to populate cache
        service.load_document("content_guidelines")
        service.load_document("templates", "python")
        
        stats = service.get_document_stats()
        
        assert stats["total_general_docs"] == 2
        assert stats["total_subject_docs"] == 1
        assert stats["cached_documents"] == 2
        assert "python" in stats["available_subjects"]
        assert stats["path_exists"] is True
    
    def test_service_with_nonexistent_path(self):
        """Test service behavior with non-existent RAG docs path"""
        service = RAGDocumentService("/nonexistent/path")
        
        # Should not crash, but return empty results
        content = service.load_document("any_doc")
        assert content == ""
        
        available = service.get_available_documents()
        assert available["general"] == []
        assert available["subjects"] == []
        
        stats = service.get_document_stats()
        # Path exists now because service creates directories automatically
        assert stats["path_exists"] is True
    
    def test_create_document_version(self, temp_rag_dir):
        """Test creating new document versions"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Create a new version
        new_content = "# Updated Content\n\nThis is version 2"
        version = service.create_document_version(
            "content_guidelines", 
            new_content, 
            "Updated content for testing",
            "test_user"
        )
        
        assert version == "1.1"
        
        # Verify new content is loaded
        current_content = service.load_document("content_guidelines")
        assert current_content == new_content
        
        # Verify version history
        versions = service.get_document_versions("content_guidelines")
        assert versions["current_version"] == "1.1"
        assert "1.0" in versions["versions"]
        assert "1.1" in versions["versions"]
        assert versions["versions"]["1.1"]["author"] == "test_user"
    
    def test_load_document_version(self, temp_rag_dir):
        """Test loading specific document versions"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Get original content
        original_content = service.load_document("content_guidelines")
        
        # Create new version
        new_content = "# Version 2 Content"
        service.create_document_version("content_guidelines", new_content)
        
        # Load original version
        v1_content = service.load_document_version("content_guidelines", "1.0")
        assert v1_content == original_content
        
        # Load current version
        v2_content = service.load_document_version("content_guidelines", "1.1")
        assert v2_content == new_content
    
    def test_rollback_document(self, temp_rag_dir):
        """Test rolling back to previous version"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Get original content
        original_content = service.load_document("content_guidelines")
        
        # Create new version
        new_content = "# Version 2 Content"
        service.create_document_version("content_guidelines", new_content)
        
        # Verify new content is current
        assert service.load_document("content_guidelines") == new_content
        
        # Rollback to version 1.0
        success = service.rollback_document("content_guidelines", "1.0")
        assert success is True
        
        # Verify rollback worked (should be version 1.2 with original content)
        current_content = service.load_document("content_guidelines")
        assert current_content == original_content
        
        versions = service.get_document_versions("content_guidelines")
        assert versions["current_version"] == "1.2"
    
    def test_compare_document_versions(self, temp_rag_dir):
        """Test comparing document versions"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Create new version with different content
        new_content = "# Short content"
        service.create_document_version("content_guidelines", new_content)
        
        # Compare versions
        comparison = service.compare_document_versions("content_guidelines", "1.0", "1.1")
        
        assert comparison["version1"] == "1.0"
        assert comparison["version2"] == "1.1"
        assert comparison["identical"] is False
        assert comparison["version2_length"] < comparison["version1_length"]  # New content is shorter
    
    def test_delete_document_version(self, temp_rag_dir):
        """Test deleting document versions"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Create multiple versions
        service.create_document_version("content_guidelines", "Version 2")
        service.create_document_version("content_guidelines", "Version 3")
        
        # Cannot delete current version
        success = service.delete_document_version("content_guidelines", "1.2")
        assert success is False
        
        # Can delete old version
        success = service.delete_document_version("content_guidelines", "1.0")
        assert success is True
        
        # Verify version is gone
        versions = service.get_document_versions("content_guidelines")
        assert "1.0" not in versions["versions"]
        assert "1.1" in versions["versions"]
        assert "1.2" in versions["versions"]
    
    def test_subject_specific_versioning(self, temp_rag_dir):
        """Test versioning for subject-specific documents"""
        service = RAGDocumentService(temp_rag_dir)
        
        # Create new version for python templates
        new_content = "# Updated Python Templates"
        version = service.create_document_version(
            "templates", 
            new_content, 
            "Updated Python templates",
            "test_user",
            "python"
        )
        
        assert version == "1.1"
        
        # Verify subject-specific versioning
        versions = service.get_document_versions("templates", "python")
        assert versions["subject"] == "python"
        assert versions["current_version"] == "1.1"
        
        # Load specific version
        content = service.load_document_version("templates", "1.1", "python")
        assert content == new_content