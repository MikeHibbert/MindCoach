"""
RAG Document Management Service
"""
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class RAGDocumentService:
    """Service for loading and managing RAG documents"""
    
    def __init__(self, rag_docs_path: str = "rag_docs"):
        """Initialize the RAG document service"""
        self.rag_docs_path = Path(rag_docs_path)
        self._document_cache = {}
        
        if not self.rag_docs_path.exists():
            logger.warning(f"RAG documents directory not found: {self.rag_docs_path}")
        else:
            logger.info(f"RAG document service initialized with path: {self.rag_docs_path}")
    
    def load_document(self, doc_type: str, subject: Optional[str] = None) -> str:
        """
        Load a specific RAG document
        
        Args:
            doc_type: Type of document (content_guidelines, survey_guidelines, etc.)
            subject: Optional subject for subject-specific templates
            
        Returns:
            Document content as string
        """
        cache_key = f"{doc_type}_{subject}" if subject else doc_type
        
        # Check cache first
        if cache_key in self._document_cache:
            logger.debug(f"Returning cached document: {cache_key}")
            return self._document_cache[cache_key]
        
        try:
            if subject:
                # Load subject-specific document
                doc_path = self.rag_docs_path / "subjects" / f"{subject}_templates.md"
            else:
                # Load general document
                doc_path = self.rag_docs_path / f"{doc_type}.md"
            
            if not doc_path.exists():
                logger.warning(f"RAG document not found: {doc_path}")
                return ""
            
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cache the document
            self._document_cache[cache_key] = content
            logger.debug(f"Loaded and cached RAG document: {cache_key}")
            
            return content
            
        except Exception as e:
            logger.error(f"Error loading RAG document {cache_key}: {e}")
            return ""
    
    def load_documents_for_stage(self, stage: str, subject: Optional[str] = None) -> List[str]:
        """
        Load all relevant documents for a specific pipeline stage
        
        Args:
            stage: Pipeline stage (survey, curriculum, lesson_plans, content)
            subject: Optional subject for subject-specific templates
            
        Returns:
            List of document contents
        """
        documents = []
        
        # Define document mappings for each stage
        stage_documents = {
            'survey': ['survey_guidelines'],
            'curriculum': ['curriculum_guidelines'],
            'lesson_plans': ['lesson_plan_guidelines'],
            'content': ['content_guidelines']
        }
        
        # Load general documents for the stage
        for doc_type in stage_documents.get(stage, []):
            doc_content = self.load_document(doc_type)
            if doc_content:
                documents.append(doc_content)
        
        # Load subject-specific templates if subject is provided
        if subject:
            subject_content = self.load_document('templates', subject)
            if subject_content:
                documents.append(subject_content)
        
        logger.info(f"Loaded {len(documents)} RAG documents for stage '{stage}' and subject '{subject}'")
        return documents
    
    def get_available_documents(self) -> Dict[str, List[str]]:
        """
        Get list of available RAG documents
        
        Returns:
            Dictionary with document types and available files
        """
        available_docs = {
            'general': [],
            'subjects': []
        }
        
        try:
            # List general documents
            if self.rag_docs_path.exists():
                for file_path in self.rag_docs_path.glob("*.md"):
                    if file_path.name != "README.md":
                        available_docs['general'].append(file_path.stem)
            
            # List subject-specific documents
            subjects_path = self.rag_docs_path / "subjects"
            if subjects_path.exists():
                for file_path in subjects_path.glob("*_templates.md"):
                    subject_name = file_path.stem.replace('_templates', '')
                    available_docs['subjects'].append(subject_name)
            
            logger.debug(f"Available RAG documents: {available_docs}")
            
        except Exception as e:
            logger.error(f"Error listing available documents: {e}")
        
        return available_docs
    
    def validate_document_structure(self, doc_type: str, content: str) -> Dict[str, bool]:
        """
        Validate that a document has the expected structure
        
        Args:
            doc_type: Type of document to validate
            content: Document content to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'has_content': bool(content.strip()),
            'has_headers': '##' in content,
            'has_examples': '```' in content,
            'proper_format': True
        }
        
        # Document-specific validations
        if doc_type == 'survey_guidelines':
            validation_results['has_question_format'] = 'multiple_choice' in content
            validation_results['has_difficulty_levels'] = all(
                level in content for level in ['beginner', 'intermediate', 'advanced']
            )
        
        elif doc_type == 'content_guidelines':
            validation_results['has_lesson_structure'] = 'Lesson Structure Template' in content
            validation_results['has_exercise_format'] = 'Exercise' in content
        
        elif doc_type == 'curriculum_guidelines':
            validation_results['has_json_format'] = '"curriculum"' in content
            validation_results['has_skill_levels'] = 'Beginner Level' in content
        
        elif doc_type == 'lesson_plan_guidelines':
            validation_results['has_time_allocation'] = 'minutes' in content
            validation_results['has_objectives'] = 'learning_objectives' in content
        
        # Overall validation
        validation_results['is_valid'] = all(validation_results.values())
        
        logger.debug(f"Document validation for {doc_type}: {validation_results}")
        return validation_results
    
    def clear_cache(self):
        """Clear the document cache"""
        self._document_cache.clear()
        logger.info("RAG document cache cleared")
    
    def reload_document(self, doc_type: str, subject: Optional[str] = None):
        """
        Reload a specific document from disk
        
        Args:
            doc_type: Type of document to reload
            subject: Optional subject for subject-specific templates
        """
        cache_key = f"{doc_type}_{subject}" if subject else doc_type
        
        # Remove from cache
        if cache_key in self._document_cache:
            del self._document_cache[cache_key]
        
        # Reload from disk
        content = self.load_document(doc_type, subject)
        logger.info(f"Reloaded RAG document: {cache_key}")
        
        return content
    
    def get_document_stats(self) -> Dict[str, any]:
        """
        Get statistics about loaded documents
        
        Returns:
            Dictionary with document statistics
        """
        available_docs = self.get_available_documents()
        
        stats = {
            'total_general_docs': len(available_docs['general']),
            'total_subject_docs': len(available_docs['subjects']),
            'cached_documents': len(self._document_cache),
            'available_subjects': available_docs['subjects'],
            'rag_docs_path': str(self.rag_docs_path),
            'path_exists': self.rag_docs_path.exists()
        }
        
        return stats

# Global instance for use across the application
rag_service = RAGDocumentService()