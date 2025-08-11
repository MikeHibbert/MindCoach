import RAGDocumentService from '../ragDocumentService';

// Mock fetch
global.fetch = jest.fn();

describe('RAGDocumentService', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('getAvailableDocuments makes correct API call', async () => {
    const mockResponse = {
      status: 'success',
      available_documents: {
        general: ['content_guidelines'],
        subjects: ['python']
      }
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const result = await RAGDocumentService.getAvailableDocuments();

    expect(fetch).toHaveBeenCalledWith('/api/rag-docs');
    expect(result).toEqual(mockResponse);
  });

  test('getDocument makes correct API call with subject', async () => {
    const mockResponse = {
      status: 'success',
      content: '# Test Content'
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const result = await RAGDocumentService.getDocument('templates', 'python');

    // Check that fetch was called with a URL containing the expected path and query
    expect(fetch).toHaveBeenCalledWith(
      expect.stringMatching(/api\/rag-docs\/templates\?subject=python$/)
    );
    expect(result).toEqual(mockResponse);
  });

  test('createDocumentVersion makes correct API call', async () => {
    const mockResponse = {
      status: 'success',
      new_version: '1.1'
    };

    const requestData = {
      content: '# New Content',
      description: 'Updated content',
      author: 'admin'
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const result = await RAGDocumentService.createDocumentVersion('content_guidelines', requestData);

    expect(fetch).toHaveBeenCalledWith('/api/rag-docs/content_guidelines/versions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData)
    });
    expect(result).toEqual(mockResponse);
  });

  test('handles API errors correctly', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      statusText: 'Not Found'
    });

    await expect(RAGDocumentService.getDocument('nonexistent'))
      .rejects.toThrow('Failed to get document: Not Found');
  });

  test('rollbackDocument makes correct API call', async () => {
    const mockResponse = {
      status: 'success',
      message: 'Successfully rolled back'
    };

    const requestData = {
      target_version: '1.0',
      subject: null
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const result = await RAGDocumentService.rollbackDocument('content_guidelines', requestData);

    expect(fetch).toHaveBeenCalledWith('/api/rag-docs/content_guidelines/rollback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData)
    });
    expect(result).toEqual(mockResponse);
  });
});