/**
 * Service for managing RAG documents
 */
class RAGDocumentService {
  static baseUrl = '/api/rag-docs';

  /**
   * Get list of available RAG documents
   */
  static async getAvailableDocuments() {
    const response = await fetch(`${this.baseUrl}`);
    if (!response.ok) {
      throw new Error(`Failed to get available documents: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get a specific RAG document
   */
  static async getDocument(docType, subject = null) {
    const url = new URL(`${this.baseUrl}/${docType}`, window.location.origin);
    if (subject) {
      url.searchParams.append('subject', subject);
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to get document: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Validate a RAG document
   */
  static async validateDocument(docType, data) {
    const response = await fetch(`${this.baseUrl}/${docType}/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to validate document: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get documents for a specific pipeline stage
   */
  static async getDocumentsForStage(stage, subject = null) {
    const url = new URL(`${this.baseUrl}/stage/${stage}`, window.location.origin);
    if (subject) {
      url.searchParams.append('subject', subject);
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to get documents for stage: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Clear document cache
   */
  static async clearCache() {
    const response = await fetch(`${this.baseUrl}/cache/clear`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`Failed to clear cache: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Reload a specific document
   */
  static async reloadDocument(docType, subject = null) {
    const response = await fetch(`${this.baseUrl}/${docType}/reload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ subject }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to reload document: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get document statistics
   */
  static async getStatistics() {
    const response = await fetch(`${this.baseUrl}/stats`);
    if (!response.ok) {
      throw new Error(`Failed to get statistics: ${response.statusText}`);
    }
    return response.json();
  }

  // Version Management Methods

  /**
   * Get version history for a document
   */
  static async getDocumentVersions(docType, subject = null) {
    const url = new URL(`${this.baseUrl}/${docType}/versions`, window.location.origin);
    if (subject) {
      url.searchParams.append('subject', subject);
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to get document versions: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get a specific version of a document
   */
  static async getDocumentVersion(docType, version, subject = null) {
    const url = new URL(`${this.baseUrl}/${docType}/versions/${version}`, window.location.origin);
    if (subject) {
      url.searchParams.append('subject', subject);
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to get document version: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Create a new version of a document
   */
  static async createDocumentVersion(docType, data) {
    const response = await fetch(`${this.baseUrl}/${docType}/versions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create document version: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Rollback a document to a previous version
   */
  static async rollbackDocument(docType, data) {
    const response = await fetch(`${this.baseUrl}/${docType}/rollback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to rollback document: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Compare two versions of a document
   */
  static async compareDocumentVersions(docType, data) {
    const response = await fetch(`${this.baseUrl}/${docType}/versions/compare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to compare document versions: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Delete a specific version of a document
   */
  static async deleteDocumentVersion(docType, version, data = {}) {
    const response = await fetch(`${this.baseUrl}/${docType}/versions/${version}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete document version: ${response.statusText}`);
    }
    return response.json();
  }
}

export default RAGDocumentService;