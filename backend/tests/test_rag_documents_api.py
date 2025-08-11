"""
Integration tests for RAG Documents API endpoints
"""
import pytest
import json
import tempfile
from pathlib import Path
from app import create_app
from app.services.rag_document_service import RAGDocumentService

class TestRAGDocumentsAPI:
    """Test RAG Documents API endpoints"""
    
    # Use the existing app and client fixtures from conftest.py
    
    @pytest.fixture
    def temp_rag_dir(self):
        """Create temporary RAG documents directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            rag_path = Path(temp_dir) / "rag_docs"
            rag_path.mkdir()
            
            # Create test documents
            (rag_path / "content_guidelines.md").write_text(
                "# Content Guidelines\n\n## Lesson Structure Template\n\n```python\ncode example\n```"
            )
            
            # Create subjects directory
            subjects_path = rag_path / "subjects"
            subjects_path.mkdir()
            
            (subjects_path / "python_templates.md").write_text(
                "# Python Templates\n\n## Python-specific content"
            )
            
            yield str(rag_path)
    
    def test_get_available_documents(self, client, temp_rag_dir, monkeypatch):
        """Test getting available documents"""
        # Mock the RAG service to use temp directory
        test_service = RAGDocumentService(temp_rag_dir)
        monkeypatch.setattr('app.api.rag_documents.rag_service', test_service)
        
        response = client.get('/api/rag-docs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'content_guidelines' in data['available_documents']['general']
        assert 'python' in data['available_documents']['subjects']
    
    def test_get_document(self, client, temp_rag_dir, monkeypatch):
        """Test getting a specific document"""
        test_service = RAGDocumentService(temp_rag_dir)
        monkeypatch.setattr('app.api.rag_documents.rag_service', test_service)
        
        response = client.get('/api/rag-docs/content_guidelines')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'Content Guidelines' in data['content']
    
    def test_get_subject_document(self, client, temp_rag_dir, monkeypatch):
        """Test getting a subject-specific document"""
        test_service = RAGDocumentService(temp_rag_dir)
        monkeypatch.setattr('app.api.rag_documents.rag_service', test_service)
        
        response = client.get('/api/rag-docs/templates?subject=python')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'Python Templates' in data['content']
    
    def test_validate_document(self, client, temp_rag_dir, monkeypatch):
        """Test document validation"""
        test_service = RAGDocumentService(temp_rag_dir)
        monkeypatch.setattr('app.api.rag_documents.rag_service', test_service)
        
        response = client.post('/api/rag-docs/content_guidelines/validate', 
                             json={'content': '# Test Content\n\n## Header\n\n```code```'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'validation_results' in data
    
    def test_create_document_version(self, client, temp_rag_dir, monkeypatch):
        """Test creating a new document version"""
        test_service = RAGDocumentService(temp_rag_dir)
        monkeypatch.setattr('app.api.rag_documents.rag_service', test_service)
        
        new_content = "# Updated Content\n\n## New Section\n\n```python\nprint('hello')\n```"
        
        response = client.post('/api/rag-docs/content_guidelines/versions', 
                             json={
                                 'content': new_content,
                                 'description': 'Test update',
                                 'author': 'test_user'
                             })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['new_version'] == '1.1'
    
    def test_get_document_versions(self, client, temp_rag_dir, monkeypatch):
        """Test getting document version history"""
        test_service = RAGDocumentService(temp_rag_dir)
        monkeypatch.setattr('app.api.rag_documents.rag_service', test_service)
        
        # Create a version first
        test_service.create_document_version(
            'content_guidelines', 
            '# New Content', 
            'Test version'
        )
        
        response = client.get('/api/rag-docs/content_guidelines/versions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['total_versions'] >= 1
        assert 'versions' in data
    
    def test_rollback_document(self, client, temp_rag_dir, monkeypatch):
        """Test rolling back a document"""
        test_service = RAGDocumentService(temp_rag_dir)
        monkeypatch.setattr('app.api.rag_documents.rag_service', test_service)
        
        # Create a version first
        test_service.create_document_version(
            'content_guidelines', 
            '# New Content', 
            'Test version'
        )
        
        response = client.post('/api/rag-docs/content_guidelines/rollback',
                             json={'target_version': '1.0'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_compare_document_versions(self, client, temp_rag_dir, monkeypatch):
        """Test comparing document versions"""
        test_service = RAGDocumentService(temp_rag_dir)
        monkeypatch.setattr('app.api.rag_documents.rag_service', test_service)
        
        # Create a version first
        test_service.create_document_version(
            'content_guidelines', 
            '# Short content', 
            'Test version'
        )
        
        response = client.post('/api/rag-docs/content_guidelines/versions/compare',
                             json={
                                 'version1': '1.0',
                                 'version2': '1.1'
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'comparison' in data
        assert data['comparison']['version1'] == '1.0'
        assert data['comparison']['version2'] == '1.1'
    
    def test_error_handling(self, client, temp_rag_dir, monkeypatch):
        """Test API error handling"""
        test_service = RAGDocumentService(temp_rag_dir)
        monkeypatch.setattr('app.api.rag_documents.rag_service', test_service)
        
        # Test non-existent document
        response = client.get('/api/rag-docs/nonexistent')
        assert response.status_code == 404
        
        # Test invalid validation request
        response = client.post('/api/rag-docs/content_guidelines/validate', json={})
        assert response.status_code == 400
        
        # Test invalid version creation
        response = client.post('/api/rag-docs/content_guidelines/versions', json={})
        assert response.status_code == 400