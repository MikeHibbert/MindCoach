"""
RAG Document Management Service
"""
import os
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class RAGDocumentService:
    """Service for loading and managing RAG documents with versioning support"""
    
    def __init__(self, rag_docs_path: str = "rag_docs"):
        """Initialize the RAG document service"""
        self.rag_docs_path = Path(rag_docs_path)
        self.versions_path = self.rag_docs_path / "versions"
        self.metadata_path = self.rag_docs_path / "metadata"
        self._document_cache = {}
        
        # Create necessary directories
        self._ensure_directories()
        
        if not self.rag_docs_path.exists():
            logger.warning(f"RAG documents directory not found: {self.rag_docs_path}")
        else:
            logger.info(f"RAG document service initialized with path: {self.rag_docs_path}")
    
    def _ensure_directories(self):
        """Ensure all necessary directories exist"""
        try:
            self.rag_docs_path.mkdir(parents=True, exist_ok=True)
            self.versions_path.mkdir(parents=True, exist_ok=True)
            self.metadata_path.mkdir(parents=True, exist_ok=True)
            
            # Create subjects directory if it doesn't exist
            subjects_path = self.rag_docs_path / "subjects"
            subjects_path.mkdir(exist_ok=True)
            
        except Exception as e:
            logger.error(f"Error creating RAG document directories: {e}")
    
    def _get_document_metadata_path(self, doc_type: str, subject: Optional[str] = None) -> Path:
        """Get the metadata file path for a document"""
        if subject:
            return self.metadata_path / f"{subject}_{doc_type}_metadata.json"
        else:
            return self.metadata_path / f"{doc_type}_metadata.json"
    
    def _get_document_version_path(self, doc_type: str, version: str, subject: Optional[str] = None) -> Path:
        """Get the version file path for a document"""
        if subject:
            return self.versions_path / f"{subject}_{doc_type}_v{version}.md"
        else:
            return self.versions_path / f"{doc_type}_v{version}.md"
    
    def _load_document_metadata(self, doc_type: str, subject: Optional[str] = None) -> Dict:
        """Load metadata for a document"""
        metadata_path = self._get_document_metadata_path(doc_type, subject)
        
        if not metadata_path.exists():
            # Create default metadata
            default_metadata = {
                "document_type": doc_type,
                "subject": subject,
                "current_version": "1.0",
                "versions": {
                    "1.0": {
                        "created_at": datetime.now().isoformat(),
                        "description": "Initial version",
                        "author": "system"
                    }
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            try:
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(default_metadata, f, indent=2)
                logger.info(f"Created default metadata for {doc_type}")
            except Exception as e:
                logger.error(f"Error creating metadata for {doc_type}: {e}")
                return default_metadata
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata for {doc_type}: {e}")
            return {}
    
    def _save_document_metadata(self, doc_type: str, metadata: Dict, subject: Optional[str] = None):
        """Save metadata for a document"""
        metadata_path = self._get_document_metadata_path(doc_type, subject)
        
        try:
            metadata["updated_at"] = datetime.now().isoformat()
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            logger.debug(f"Saved metadata for {doc_type}")
        except Exception as e:
            logger.error(f"Error saving metadata for {doc_type}: {e}")
    
    def _get_document_path(self, doc_type: str, subject: Optional[str] = None) -> Path:
        """Get the current document file path"""
        if subject:
            return self.rag_docs_path / "subjects" / f"{subject}_templates.md"
        else:
            return self.rag_docs_path / f"{doc_type}.md"
    
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
            'path_exists': self.rag_docs_path.exists(),
            'versions_path': str(self.versions_path),
            'metadata_path': str(self.metadata_path)
        }
        
        return stats
    
    def create_document_version(self, doc_type: str, content: str, description: str = "", 
                              author: str = "system", subject: Optional[str] = None) -> str:
        """
        Create a new version of a document
        
        Args:
            doc_type: Type of document
            content: New document content
            description: Description of changes
            author: Author of the changes
            subject: Optional subject for subject-specific documents
            
        Returns:
            New version number
        """
        try:
            # Load current metadata
            metadata = self._load_document_metadata(doc_type, subject)
            
            # Generate new version number
            current_version = metadata.get("current_version", "1.0")
            version_parts = current_version.split(".")
            major, minor = int(version_parts[0]), int(version_parts[1])
            new_version = f"{major}.{minor + 1}"
            
            # Save current version to versions directory
            current_doc_path = self._get_document_path(doc_type, subject)
            if current_doc_path.exists():
                current_content = current_doc_path.read_text(encoding='utf-8')
                version_path = self._get_document_version_path(doc_type, current_version, subject)
                version_path.write_text(current_content, encoding='utf-8')
                logger.info(f"Backed up current version {current_version} to {version_path}")
            
            # Save new content as current version
            current_doc_path.parent.mkdir(parents=True, exist_ok=True)
            current_doc_path.write_text(content, encoding='utf-8')
            
            # Update metadata
            metadata["current_version"] = new_version
            metadata["versions"][new_version] = {
                "created_at": datetime.now().isoformat(),
                "description": description or f"Version {new_version}",
                "author": author,
                "content_length": len(content)
            }
            
            self._save_document_metadata(doc_type, metadata, subject)
            
            # Clear cache for this document
            cache_key = f"{doc_type}_{subject}" if subject else doc_type
            if cache_key in self._document_cache:
                del self._document_cache[cache_key]
            
            logger.info(f"Created new version {new_version} for document {doc_type}")
            return new_version
            
        except Exception as e:
            logger.error(f"Error creating document version for {doc_type}: {e}")
            raise
    
    def get_document_versions(self, doc_type: str, subject: Optional[str] = None) -> Dict:
        """
        Get version history for a document
        
        Args:
            doc_type: Type of document
            subject: Optional subject for subject-specific documents
            
        Returns:
            Dictionary with version information
        """
        try:
            metadata = self._load_document_metadata(doc_type, subject)
            return {
                "document_type": doc_type,
                "subject": subject,
                "current_version": metadata.get("current_version", "1.0"),
                "versions": metadata.get("versions", {}),
                "total_versions": len(metadata.get("versions", {}))
            }
        except Exception as e:
            logger.error(f"Error getting versions for {doc_type}: {e}")
            return {}
    
    def load_document_version(self, doc_type: str, version: str, subject: Optional[str] = None) -> str:
        """
        Load a specific version of a document
        
        Args:
            doc_type: Type of document
            version: Version to load
            subject: Optional subject for subject-specific documents
            
        Returns:
            Document content for the specified version
        """
        try:
            metadata = self._load_document_metadata(doc_type, subject)
            
            # Check if version exists
            if version not in metadata.get("versions", {}):
                logger.warning(f"Version {version} not found for document {doc_type}")
                return ""
            
            # If requesting current version, load from main file
            current_version = metadata.get("current_version", "1.0")
            if version == current_version:
                return self.load_document(doc_type, subject)
            
            # Load from versions directory
            version_path = self._get_document_version_path(doc_type, version, subject)
            if not version_path.exists():
                logger.warning(f"Version file not found: {version_path}")
                return ""
            
            content = version_path.read_text(encoding='utf-8')
            logger.debug(f"Loaded version {version} for document {doc_type}")
            return content
            
        except Exception as e:
            logger.error(f"Error loading version {version} for {doc_type}: {e}")
            return ""
    
    def rollback_document(self, doc_type: str, target_version: str, subject: Optional[str] = None) -> bool:
        """
        Rollback a document to a previous version
        
        Args:
            doc_type: Type of document
            target_version: Version to rollback to
            subject: Optional subject for subject-specific documents
            
        Returns:
            True if rollback was successful
        """
        try:
            # Load target version content
            target_content = self.load_document_version(doc_type, target_version, subject)
            if not target_content:
                logger.error(f"Cannot rollback: target version {target_version} not found")
                return False
            
            # Create new version with rollback content
            description = f"Rollback to version {target_version}"
            new_version = self.create_document_version(
                doc_type, target_content, description, "system", subject
            )
            
            logger.info(f"Successfully rolled back {doc_type} to version {target_version} (new version: {new_version})")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back {doc_type} to version {target_version}: {e}")
            return False
    
    def compare_document_versions(self, doc_type: str, version1: str, version2: str, 
                                subject: Optional[str] = None) -> Dict:
        """
        Compare two versions of a document
        
        Args:
            doc_type: Type of document
            version1: First version to compare
            version2: Second version to compare
            subject: Optional subject for subject-specific documents
            
        Returns:
            Dictionary with comparison results
        """
        try:
            content1 = self.load_document_version(doc_type, version1, subject)
            content2 = self.load_document_version(doc_type, version2, subject)
            
            if not content1 or not content2:
                return {
                    "error": "One or both versions not found",
                    "version1_found": bool(content1),
                    "version2_found": bool(content2)
                }
            
            # Basic comparison metrics
            lines1 = content1.split('\n')
            lines2 = content2.split('\n')
            
            comparison = {
                "document_type": doc_type,
                "subject": subject,
                "version1": version1,
                "version2": version2,
                "version1_length": len(content1),
                "version2_length": len(content2),
                "version1_lines": len(lines1),
                "version2_lines": len(lines2),
                "length_difference": len(content2) - len(content1),
                "lines_difference": len(lines2) - len(lines1),
                "identical": content1 == content2
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing versions for {doc_type}: {e}")
            return {"error": str(e)}
    
    def delete_document_version(self, doc_type: str, version: str, subject: Optional[str] = None) -> bool:
        """
        Delete a specific version of a document (cannot delete current version)
        
        Args:
            doc_type: Type of document
            version: Version to delete
            subject: Optional subject for subject-specific documents
            
        Returns:
            True if deletion was successful
        """
        try:
            metadata = self._load_document_metadata(doc_type, subject)
            current_version = metadata.get("current_version", "1.0")
            
            # Cannot delete current version
            if version == current_version:
                logger.error(f"Cannot delete current version {version}")
                return False
            
            # Check if version exists
            if version not in metadata.get("versions", {}):
                logger.warning(f"Version {version} not found for document {doc_type}")
                return False
            
            # Delete version file
            version_path = self._get_document_version_path(doc_type, version, subject)
            if version_path.exists():
                version_path.unlink()
                logger.info(f"Deleted version file: {version_path}")
            
            # Remove from metadata
            del metadata["versions"][version]
            self._save_document_metadata(doc_type, metadata, subject)
            
            logger.info(f"Successfully deleted version {version} for document {doc_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting version {version} for {doc_type}: {e}")
            return False

# Global instance for use across the application
rag_service = RAGDocumentService()