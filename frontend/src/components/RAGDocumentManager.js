import React, { useState, useEffect } from 'react';
import RAGDocumentService from '../services/ragDocumentService';

const RAGDocumentManager = () => {
  const [documents, setDocuments] = useState({ general: [], subjects: [] });
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [content, setContent] = useState('');
  const [versions, setVersions] = useState(null);
  const [selectedVersion, setSelectedVersion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('edit');
  const [validationResults, setValidationResults] = useState(null);
  const [compareVersions, setCompareVersions] = useState({ version1: '', version2: '' });
  const [comparisonResult, setComparisonResult] = useState(null);

  useEffect(() => {
    loadAvailableDocuments();
  }, []);

  const loadAvailableDocuments = async () => {
    try {
      setLoading(true);
      const response = await RAGDocumentService.getAvailableDocuments();
      setDocuments(response.available_documents);
      setError('');
    } catch (err) {
      setError('Failed to load available documents: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadDocument = async (docType, subject = null) => {
    try {
      setLoading(true);
      const response = await RAGDocumentService.getDocument(docType, subject);
      setContent(response.content);
      setSelectedDoc(docType);
      setSelectedSubject(subject || '');
      
      // Load versions
      const versionsResponse = await RAGDocumentService.getDocumentVersions(docType, subject);
      setVersions(versionsResponse);
      setSelectedVersion(versionsResponse.current_version);
      
      setError('');
      setSuccess('');
    } catch (err) {
      setError('Failed to load document: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadDocumentVersion = async (version) => {
    if (!selectedDoc || !version) return;
    
    try {
      setLoading(true);
      const response = await RAGDocumentService.getDocumentVersion(
        selectedDoc, 
        version, 
        selectedSubject || null
      );
      setContent(response.content);
      setSelectedVersion(version);
      setError('');
    } catch (err) {
      setError('Failed to load document version: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const validateDocument = async () => {
    if (!selectedDoc || !content) return;
    
    try {
      setLoading(true);
      const response = await RAGDocumentService.validateDocument(selectedDoc, {
        content,
        subject: selectedSubject || null
      });
      setValidationResults(response.validation_results);
      setError('');
    } catch (err) {
      setError('Failed to validate document: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const saveDocument = async () => {
    if (!selectedDoc || !content) return;
    
    try {
      setLoading(true);
      const description = prompt('Enter a description for this version:') || 'Updated via admin interface';
      
      const response = await RAGDocumentService.createDocumentVersion(selectedDoc, {
        content,
        description,
        author: 'admin',
        subject: selectedSubject || null
      });
      
      setSuccess(`Created new version ${response.new_version}`);
      
      // Reload versions
      const versionsResponse = await RAGDocumentService.getDocumentVersions(
        selectedDoc, 
        selectedSubject || null
      );
      setVersions(versionsResponse);
      setSelectedVersion(versionsResponse.current_version);
      
      setError('');
    } catch (err) {
      setError('Failed to save document: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const rollbackDocument = async (targetVersion) => {
    if (!selectedDoc || !targetVersion) return;
    
    if (!window.confirm(`Are you sure you want to rollback to version ${targetVersion}?`)) {
      return;
    }
    
    try {
      setLoading(true);
      await RAGDocumentService.rollbackDocument(selectedDoc, {
        target_version: targetVersion,
        subject: selectedSubject || null
      });
      
      setSuccess(`Successfully rolled back to version ${targetVersion}`);
      
      // Reload document and versions
      await loadDocument(selectedDoc, selectedSubject || null);
      
      setError('');
    } catch (err) {
      setError('Failed to rollback document: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const compareDocumentVersions = async () => {
    if (!selectedDoc || !compareVersions.version1 || !compareVersions.version2) return;
    
    try {
      setLoading(true);
      const response = await RAGDocumentService.compareDocumentVersions(selectedDoc, {
        version1: compareVersions.version1,
        version2: compareVersions.version2,
        subject: selectedSubject || null
      });
      setComparisonResult(response.comparison);
      setError('');
    } catch (err) {
      setError('Failed to compare versions: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteVersion = async (version) => {
    if (!selectedDoc || !version) return;
    
    if (!window.confirm(`Are you sure you want to delete version ${version}?`)) {
      return;
    }
    
    try {
      setLoading(true);
      await RAGDocumentService.deleteDocumentVersion(selectedDoc, version, {
        subject: selectedSubject || null
      });
      
      setSuccess(`Successfully deleted version ${version}`);
      
      // Reload versions
      const versionsResponse = await RAGDocumentService.getDocumentVersions(
        selectedDoc, 
        selectedSubject || null
      );
      setVersions(versionsResponse);
      
      setError('');
    } catch (err) {
      setError('Failed to delete version: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 bg-white">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">RAG Document Management</h1>
      
      {/* Error/Success Messages */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
          {success}
        </div>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Document Selection Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h2 className="text-lg font-semibold mb-4">Documents</h2>
            
            {/* General Documents */}
            <div className="mb-6">
              <h3 className="text-md font-medium text-gray-700 mb-2">General</h3>
              <div className="space-y-1">
                {documents.general.map(doc => (
                  <button
                    key={doc}
                    onClick={() => loadDocument(doc)}
                    className={`w-full text-left px-3 py-2 rounded text-sm ${
                      selectedDoc === doc && !selectedSubject
                        ? 'bg-blue-100 text-blue-800'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    {doc.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Subject-Specific Documents */}
            <div>
              <h3 className="text-md font-medium text-gray-700 mb-2">Subjects</h3>
              <div className="space-y-1">
                {documents.subjects.map(subject => (
                  <button
                    key={subject}
                    onClick={() => loadDocument('templates', subject)}
                    className={`w-full text-left px-3 py-2 rounded text-sm ${
                      selectedDoc === 'templates' && selectedSubject === subject
                        ? 'bg-blue-100 text-blue-800'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    {subject} templates
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* Main Content Area */}
        <div className="lg:col-span-3">
          {selectedDoc ? (
            <div>
              {/* Document Header */}
              <div className="mb-6">
                <h2 className="text-xl font-semibold">
                  {selectedDoc.replace('_', ' ')}
                  {selectedSubject && ` (${selectedSubject})`}
                </h2>
                {versions && (
                  <p className="text-gray-600">
                    Current Version: {versions.current_version} | 
                    Total Versions: {versions.total_versions}
                  </p>
                )}
              </div>
              
              {/* Tab Navigation */}
              <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex space-x-8">
                  {['edit', 'versions', 'validate', 'compare'].map(tab => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`py-2 px-1 border-b-2 font-medium text-sm ${
                        activeTab === tab
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                  ))}
                </nav>
              </div>
              
              {/* Tab Content */}
              {activeTab === 'edit' && (
                <div>
                  <div className="mb-4 flex justify-between items-center">
                    <h3 className="text-lg font-medium">Edit Document</h3>
                    <div className="space-x-2">
                      <button
                        onClick={validateDocument}
                        disabled={loading}
                        className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
                      >
                        Validate
                      </button>
                      <button
                        onClick={saveDocument}
                        disabled={loading}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                      >
                        Save New Version
                      </button>
                    </div>
                  </div>
                  
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="w-full h-96 p-4 border border-gray-300 rounded-lg font-mono text-sm"
                    placeholder="Document content..."
                  />
                </div>
              )}
              
              {activeTab === 'versions' && versions && (
                <div>
                  <h3 className="text-lg font-medium mb-4">Version History</h3>
                  
                  <div className="space-y-4">
                    {Object.entries(versions.versions).reverse().map(([version, info]) => (
                      <div key={version} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-medium">
                              Version {version}
                              {version === versions.current_version && (
                                <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                                  Current
                                </span>
                              )}
                            </h4>
                            <p className="text-sm text-gray-600">{info.description}</p>
                            <p className="text-xs text-gray-500">
                              By {info.author} on {new Date(info.created_at).toLocaleString()}
                            </p>
                          </div>
                          
                          <div className="space-x-2">
                            <button
                              onClick={() => loadDocumentVersion(version)}
                              className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
                            >
                              View
                            </button>
                            {version !== versions.current_version && (
                              <>
                                <button
                                  onClick={() => rollbackDocument(version)}
                                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200"
                                >
                                  Rollback
                                </button>
                                <button
                                  onClick={() => deleteVersion(version)}
                                  className="px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200"
                                >
                                  Delete
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {activeTab === 'validate' && (
                <div>
                  <h3 className="text-lg font-medium mb-4">Document Validation</h3>
                  
                  <button
                    onClick={validateDocument}
                    disabled={loading}
                    className="mb-4 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
                  >
                    Run Validation
                  </button>
                  
                  {validationResults && (
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium mb-2">Validation Results</h4>
                      <div className="space-y-2">
                        {Object.entries(validationResults).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="text-sm">{key.replace('_', ' ')}</span>
                            <span className={`text-sm ${value ? 'text-green-600' : 'text-red-600'}`}>
                              {value ? '✓' : '✗'}
                            </span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 p-2 rounded">
                        <span className={`font-medium ${
                          validationResults.is_valid ? 'text-green-600' : 'text-red-600'
                        }`}>
                          Overall: {validationResults.is_valid ? 'Valid' : 'Invalid'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {activeTab === 'compare' && versions && (
                <div>
                  <h3 className="text-lg font-medium mb-4">Compare Versions</h3>
                  
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Version 1
                      </label>
                      <select
                        value={compareVersions.version1}
                        onChange={(e) => setCompareVersions(prev => ({ ...prev, version1: e.target.value }))}
                        className="w-full p-2 border border-gray-300 rounded"
                      >
                        <option value="">Select version</option>
                        {Object.keys(versions.versions).map(version => (
                          <option key={version} value={version}>{version}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Version 2
                      </label>
                      <select
                        value={compareVersions.version2}
                        onChange={(e) => setCompareVersions(prev => ({ ...prev, version2: e.target.value }))}
                        className="w-full p-2 border border-gray-300 rounded"
                      >
                        <option value="">Select version</option>
                        {Object.keys(versions.versions).map(version => (
                          <option key={version} value={version}>{version}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  
                  <button
                    onClick={compareDocumentVersions}
                    disabled={loading || !compareVersions.version1 || !compareVersions.version2}
                    className="mb-4 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                  >
                    Compare Versions
                  </button>
                  
                  {comparisonResult && (
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium mb-2">Comparison Results</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <h5 className="font-medium">Version {comparisonResult.version1}</h5>
                          <p>Length: {comparisonResult.version1_length} characters</p>
                          <p>Lines: {comparisonResult.version1_lines}</p>
                        </div>
                        <div>
                          <h5 className="font-medium">Version {comparisonResult.version2}</h5>
                          <p>Length: {comparisonResult.version2_length} characters</p>
                          <p>Lines: {comparisonResult.version2_lines}</p>
                        </div>
                      </div>
                      <div className="mt-4 p-2 bg-gray-50 rounded">
                        <p className="text-sm">
                          <strong>Difference:</strong> {comparisonResult.length_difference} characters, 
                          {comparisonResult.lines_difference} lines
                        </p>
                        <p className="text-sm">
                          <strong>Identical:</strong> {comparisonResult.identical ? 'Yes' : 'No'}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">Select a document to begin editing</p>
            </div>
          )}
        </div>
      </div>
      
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-4 rounded-lg">
            <p>Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default RAGDocumentManager;