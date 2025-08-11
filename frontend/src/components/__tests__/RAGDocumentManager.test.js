import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RAGDocumentManager from '../RAGDocumentManager';
import RAGDocumentService from '../../services/ragDocumentService';

// Mock the RAG document service
jest.mock('../../services/ragDocumentService');

describe('RAGDocumentManager', () => {
  const mockDocuments = {
    general: ['content_guidelines', 'survey_guidelines'],
    subjects: ['python', 'javascript']
  };

  const mockVersions = {
    current_version: '1.1',
    total_versions: 2,
    versions: {
      '1.0': {
        created_at: '2024-01-01T10:00:00Z',
        description: 'Initial version',
        author: 'system'
      },
      '1.1': {
        created_at: '2024-01-02T10:00:00Z',
        description: 'Updated content',
        author: 'admin'
      }
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    RAGDocumentService.getAvailableDocuments.mockResolvedValue({
      available_documents: mockDocuments
    });
  });

  test('renders document manager interface', async () => {
    render(<RAGDocumentManager />);
    
    expect(screen.getByText('RAG Document Management')).toBeInTheDocument();
    expect(screen.getByText('Documents')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('content guidelines')).toBeInTheDocument();
      expect(screen.getByText('python templates')).toBeInTheDocument();
    });
  });

  test('loads document when clicked', async () => {
    const mockDocument = {
      content: '# Test Content\n\nThis is test content.',
      content_length: 30
    };

    RAGDocumentService.getDocument.mockResolvedValue(mockDocument);
    RAGDocumentService.getDocumentVersions.mockResolvedValue(mockVersions);

    render(<RAGDocumentManager />);
    
    await waitFor(() => {
      expect(screen.getByText('content guidelines')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('content guidelines'));

    await waitFor(() => {
      expect(RAGDocumentService.getDocument).toHaveBeenCalledWith('content_guidelines', null);
      expect(RAGDocumentService.getDocumentVersions).toHaveBeenCalledWith('content_guidelines', null);
    });
  });

  test('validates document content', async () => {
    const mockDocument = {
      content: '# Test Content',
      content_length: 15
    };

    const mockValidation = {
      validation_results: {
        has_content: true,
        has_headers: true,
        is_valid: true
      }
    };

    RAGDocumentService.getDocument.mockResolvedValue(mockDocument);
    RAGDocumentService.getDocumentVersions.mockResolvedValue(mockVersions);
    RAGDocumentService.validateDocument.mockResolvedValue(mockValidation);

    render(<RAGDocumentManager />);
    
    // Load a document first
    await waitFor(() => {
      expect(screen.getByText('content guidelines')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('content guidelines'));

    // Switch to validate tab - use getAllByText to handle multiple elements
    await waitFor(() => {
      expect(screen.getAllByText('Validate')[0]).toBeInTheDocument();
    });
    fireEvent.click(screen.getAllByText('Validate')[0]); // Click the tab

    // Click validate button
    await waitFor(() => {
      expect(screen.getByText('Run Validation')).toBeInTheDocument();
    });
    const validateButton = screen.getByText('Run Validation');
    fireEvent.click(validateButton);

    await waitFor(() => {
      expect(RAGDocumentService.validateDocument).toHaveBeenCalled();
    });
  });
});