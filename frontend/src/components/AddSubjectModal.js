import React, { useState } from 'react';

const AddSubjectModal = ({ isOpen, onClose, onSubmit, isLoading, userTokens }) => {
  const [subjectTitle, setSubjectTitle] = useState('');
  const [description, setDescription] = useState('');
  const [estimatedLessons, setEstimatedLessons] = useState(10);
  
  const TOKENS_REQUIRED = 50; // Cost to create a custom subject
  const hasEnoughTokens = userTokens >= TOKENS_REQUIRED;

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!subjectTitle.trim()) {
      return;
    }

    if (!hasEnoughTokens) {
      return;
    }

    onSubmit({
      title: subjectTitle.trim(),
      description: description.trim(),
      estimatedLessons: estimatedLessons
    });
  };

  const handleClose = () => {
    if (!isLoading) {
      setSubjectTitle('');
      setDescription('');
      setEstimatedLessons(10);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Create Custom Subject</h3>
          <button
            onClick={handleClose}
            disabled={isLoading}
            className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Subject Title */}
          <div>
            <label htmlFor="subject-title" className="block text-sm font-medium text-gray-700 mb-1">
              Subject Title *
            </label>
            <input
              id="subject-title"
              type="text"
              value={subjectTitle}
              onChange={(e) => setSubjectTitle(e.target.value)}
              placeholder="e.g., Machine Learning, Web Design, Photography..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
              required
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="subject-description" className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <textarea
              id="subject-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of what you want to learn..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            />
          </div>

          {/* Estimated Lessons */}
          <div>
            <label htmlFor="estimated-lessons" className="block text-sm font-medium text-gray-700 mb-1">
              Estimated Number of Lessons
            </label>
            <select
              id="estimated-lessons"
              value={estimatedLessons}
              onChange={(e) => setEstimatedLessons(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            >
              <option value={5}>5 lessons (Quick overview)</option>
              <option value={10}>10 lessons (Standard course)</option>
              <option value={15}>15 lessons (Comprehensive)</option>
              <option value={20}>20 lessons (In-depth mastery)</option>
            </select>
          </div>

          {/* Token Cost Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm">
                <p className="text-blue-800">
                  <strong>Cost:</strong> {TOKENS_REQUIRED} tokens
                </p>
                <p className="text-blue-600">
                  Your balance: {userTokens} tokens
                </p>
              </div>
            </div>
          </div>

          {/* Error message for insufficient tokens */}
          {!hasEnoughTokens && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-red-800">
                  Insufficient tokens. You need {TOKENS_REQUIRED} tokens to create a custom subject.
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !subjectTitle.trim() || !hasEnoughTokens}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating...
                </>
              ) : (
                'Create Subject'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddSubjectModal;