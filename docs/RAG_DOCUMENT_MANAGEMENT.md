# RAG Document Management System

## Overview

The RAG (Retrieval-Augmented Generation) Document Management System provides comprehensive version control, validation, and administrative capabilities for managing the documents that guide MindCoach's AI content generation pipeline.

## Features

### Version Control System
- **Automatic Versioning**: Each document update creates a new version with incremental numbering (1.0, 1.1, 1.2, etc.)
- **Version Metadata**: Tracks author, timestamp, description, and content length for each version
- **Version History**: Complete audit trail of all document changes
- **Rollback Capability**: Administrators can rollback to any previous version
- **Version Comparison**: Compare content differences between any two versions
- **Version Deletion**: Remove old versions (except current) to manage storage

### Administrative Interface
- **Web-based Management**: React-based admin interface accessible at `/admin/rag-documents`
- **Document Browser**: Organized view of general and subject-specific documents
- **Document Editor**: In-browser markdown editor with syntax highlighting
- **Real-time Validation**: Instant feedback on document structure and format
- **Tabbed Interface**: Separate tabs for editing, versions, validation, and comparison
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### Document Validation
- **Structure Validation**: Ensures required sections and formatting are present
- **Content Quality Checks**: Validates code examples, headers, and formatting standards
- **Subject-specific Rules**: Different validation rules for different document types
- **Automated Testing**: Integration tests verify document integrity

## Architecture

### File Structure
```
rag_docs/
├── content_guidelines.md             # Lesson content structure and quality standards
├── survey_guidelines.md              # Survey question formats and assessment criteria
├── curriculum_guidelines.md          # Curriculum structure and progression rules
├── lesson_plan_guidelines.md         # Lesson plan templates and requirements
├── subjects/                         # Subject-specific templates
│   ├── python_templates.md          # Python-specific content guidelines
│   ├── javascript_templates.md      # JavaScript-specific content guidelines
│   └── react_templates.md           # React-specific content guidelines
├── versions/                         # Version history storage
│   ├── content_guidelines_v1.0.md   # Previous versions of documents
│   ├── content_guidelines_v1.1.md
│   └── ...
├── metadata/                         # Version metadata and tracking
│   ├── content_guidelines_metadata.json
│   ├── survey_guidelines_metadata.json
│   └── ...
└── README.md                         # Documentation overview
```

### Backend Components

#### RAGDocumentService
The core service class that handles all document operations:

```python
from app.services.rag_document_service import RAGDocumentService

# Initialize service
rag_service = RAGDocumentService("rag_docs")

# Load current document
content = rag_service.load_document("content_guidelines")

# Create new version
new_version = rag_service.create_document_version(
    "content_guidelines",
    updated_content,
    "Added new exercise guidelines",
    "admin_user"
)

# Get version history
versions = rag_service.get_document_versions("content_guidelines")

# Rollback to previous version
success = rag_service.rollback_document("content_guidelines", "1.0")
```

#### API Endpoints
RESTful API endpoints for document management:

- `GET /api/rag-docs` - List available documents
- `GET /api/rag-docs/{doc_type}` - Get document content
- `POST /api/rag-docs/{doc_type}/validate` - Validate document structure
- `GET /api/rag-docs/{doc_type}/versions` - Get version history
- `POST /api/rag-docs/{doc_type}/versions` - Create new version
- `POST /api/rag-docs/{doc_type}/rollback` - Rollback to previous version
- `POST /api/rag-docs/{doc_type}/versions/compare` - Compare versions

### Frontend Components

#### RAGDocumentManager
React component providing the administrative interface:

```javascript
import RAGDocumentManager from './components/RAGDocumentManager';

// Usage in App.js
<Route path="/admin/rag-documents" element={<RAGDocumentManager />} />
```

#### RAGDocumentService
Frontend service for API communication:

```javascript
import RAGDocumentService from './services/ragDocumentService';

// Get available documents
const documents = await RAGDocumentService.getAvailableDocuments();

// Create new version
const result = await RAGDocumentService.createDocumentVersion('content_guidelines', {
  content: updatedContent,
  description: 'Updated formatting guidelines',
  author: 'admin'
});
```

## Usage Guide

### Accessing the Admin Interface

1. Navigate to `/admin/rag-documents` in your browser
2. Select a document from the sidebar (General or Subject-specific)
3. Use the tabbed interface to:
   - **Edit**: Modify document content
   - **Versions**: View version history and manage versions
   - **Validate**: Check document structure and format
   - **Compare**: Compare different versions

### Creating a New Document Version

1. Select the document you want to update
2. Edit the content in the **Edit** tab
3. Click **Validate** to check the document structure
4. Click **Save New Version** and provide a description
5. The system automatically creates a new version and backs up the previous one

### Rolling Back to a Previous Version

1. Go to the **Versions** tab
2. Find the version you want to rollback to
3. Click **Rollback** next to that version
4. Confirm the rollback operation
5. The system creates a new version with the content from the selected version

### Comparing Document Versions

1. Go to the **Compare** tab
2. Select two versions from the dropdown menus
3. Click **Compare Versions**
4. Review the comparison results showing differences in length, lines, and content

## Document Types

### General Documents

#### content_guidelines.md
Defines the structure and quality standards for lesson content:
- Lesson structure template
- Code example requirements
- Exercise design principles
- Markdown formatting standards

#### survey_guidelines.md
Specifies survey question formats and assessment criteria:
- Question types and formats
- Difficulty level definitions
- Assessment scoring methods
- Survey structure requirements

#### curriculum_guidelines.md
Outlines curriculum structure and progression rules:
- Learning objective formats
- Lesson progression logic
- Skill level adaptations
- Topic selection criteria

#### lesson_plan_guidelines.md
Provides lesson plan templates and requirements:
- Lesson plan structure
- Activity type definitions
- Assessment methods
- Time allocation guidelines

### Subject-Specific Documents

#### python_templates.md
Python-specific content guidelines and templates:
- Python coding standards
- Common Python patterns
- Python-specific examples
- Library and framework preferences

#### javascript_templates.md
JavaScript-specific content guidelines and templates:
- Modern JavaScript features
- Browser compatibility considerations
- Framework-specific patterns
- Best practices for web development

#### react_templates.md
React-specific content guidelines and templates:
- Component structure patterns
- Hook usage guidelines
- State management approaches
- Testing strategies for React

## Validation Rules

### General Validation
- Document must have content
- Must contain proper markdown headers
- Must include code examples where appropriate
- Must follow proper formatting standards

### Document-Specific Validation

#### Content Guidelines
- Must contain "Lesson Structure Template" section
- Must include exercise format guidelines
- Must have code quality standards

#### Survey Guidelines
- Must specify question formats (multiple_choice, etc.)
- Must define difficulty levels (beginner, intermediate, advanced)
- Must include assessment criteria

#### Curriculum Guidelines
- Must specify JSON output format
- Must include skill level definitions
- Must define progression rules

#### Lesson Plan Guidelines
- Must include time allocation guidelines
- Must specify learning objective formats
- Must define activity types

## API Reference

### Authentication
All RAG document management endpoints require administrative access. In the current implementation, no authentication is required, but this should be added for production use.

### Error Handling
The API returns consistent error responses:

```json
{
  "status": "error",
  "message": "Human-readable error message",
  "details": {
    // Additional error context
  }
}
```

### Rate Limiting
RAG document management endpoints are not currently rate-limited, but this should be implemented for production use to prevent abuse.

## Testing

### Unit Tests
- `test_rag_document_service.py` - Tests for the backend service
- `RAGDocumentManager.test.js` - Tests for the React component
- `ragDocumentService.test.js` - Tests for the frontend service

### Integration Tests
- `test_rag_documents_api.py` - Tests for API endpoints
- End-to-end tests for the complete workflow

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/test_rag_document_service.py -v

# Frontend tests
cd frontend
npm test -- --testPathPattern=RAGDocument
```

## Security Considerations

### Access Control
- Implement authentication for admin interface
- Add role-based access control
- Audit logging for document changes

### Data Validation
- Sanitize user input to prevent XSS
- Validate file paths to prevent directory traversal
- Implement content size limits

### Version Management
- Implement retention policies for old versions
- Add backup and recovery procedures
- Monitor disk usage for version storage

## Future Enhancements

### Planned Features
- **User Authentication**: Secure admin access with role-based permissions
- **Audit Logging**: Complete audit trail of all document changes
- **Backup Integration**: Automated backups to cloud storage
- **Collaborative Editing**: Multiple users editing with conflict resolution
- **Template System**: Reusable templates for new documents
- **Import/Export**: Bulk import/export of documents
- **Search Functionality**: Full-text search across all documents
- **Notification System**: Alerts for document changes and validation failures

### Technical Improvements
- **Database Storage**: Move from file system to database storage
- **Real-time Collaboration**: WebSocket-based real-time editing
- **Advanced Validation**: AI-powered content quality analysis
- **Performance Optimization**: Caching and lazy loading improvements
- **Mobile App**: Native mobile app for document management

## Troubleshooting

### Common Issues

#### Document Not Loading
- Check file permissions on rag_docs directory
- Verify document exists in the correct location
- Check server logs for file system errors

#### Version Creation Fails
- Ensure sufficient disk space for version storage
- Check write permissions on versions directory
- Verify document content is valid

#### Validation Errors
- Review document structure against validation rules
- Check for required sections and formatting
- Ensure code examples are properly formatted

#### Admin Interface Not Accessible
- Verify React route is properly configured
- Check for JavaScript errors in browser console
- Ensure API endpoints are responding correctly

### Support
For additional support or bug reports, please refer to the main project documentation or create an issue in the project repository.