import React, { useState, useEffect } from 'react';

const SubjectSelector = ({ userId, onSubjectSelect }) => {
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'dropdown'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch subjects on component mount
  useEffect(() => {
    fetchSubjects();
  }, [userId]);

  const fetchSubjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const url = userId 
        ? `/api/subjects?user_id=${encodeURIComponent(userId)}`
        : '/api/subjects';
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to fetch subjects');
      }
      
      setSubjects(data.subjects || []);
    } catch (err) {
      console.error('Error fetching subjects:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubjectSelect = async (subject) => {
    if (subject.locked) {
      // Don't allow selection of locked subjects
      return;
    }

    try {
      setError(null); // Clear any previous errors
      setSelectedSubject(subject);
      
      // Persist subject selection to backend if userId is provided
      if (userId) {
        const response = await fetch(`/api/users/${encodeURIComponent(userId)}/subjects/${encodeURIComponent(subject.id)}/select`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          const errorData = await response.json();
          
          // Handle subscription required error
          if (response.status === 402) {
            setError(`Subscription required for ${subject.name}. ${errorData.error?.message || ''}`);
            setSelectedSubject(null);
            return;
          }
          
          throw new Error(errorData.error?.message || 'Failed to select subject');
        }

        const data = await response.json();
        console.log('Subject selection saved:', data);
      }
      
      // Call parent callback if provided (always call it after successful selection)
      if (onSubjectSelect) {
        onSubjectSelect(subject);
      }
    } catch (err) {
      console.error('Error selecting subject:', err);
      setError(err.message || 'Failed to select subject');
      setSelectedSubject(null);
      // Don't call onSubjectSelect callback on error
    }
  };

  const SubjectCard = ({ subject, isSelected, onClick }) => (
    <div
      className={`
        relative p-6 rounded-lg border-2 transition-all duration-200 cursor-pointer
        ${subject.locked 
          ? 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60' 
          : isSelected
            ? 'border-primary-500 bg-primary-50 shadow-md'
            : 'border-gray-200 bg-white hover:border-primary-300 hover:shadow-sm'
        }
        ${!subject.locked ? 'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2' : ''}
      `}
      onClick={() => !subject.locked && onClick(subject)}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !subject.locked) {
          e.preventDefault();
          onClick(subject);
        }
      }}
      tabIndex={subject.locked ? -1 : 0}
      role="button"
      aria-pressed={isSelected}
      aria-disabled={subject.locked}
      aria-describedby={`subject-${subject.id}-description`}
    >
      {/* Lock indicator */}
      {subject.locked && (
        <div className="absolute top-3 right-3">
          <svg
            className="w-5 h-5 text-gray-400"
            fill="currentColor"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      )}
      
      {/* Selection indicator */}
      {isSelected && !subject.locked && (
        <div className="absolute top-3 right-3">
          <svg
            className="w-5 h-5 text-primary-600"
            fill="currentColor"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      )}

      <div className="mb-3">
        <h3 className={`text-lg font-semibold ${subject.locked ? 'text-gray-500' : 'text-gray-900'}`}>
          {subject.name}
        </h3>
      </div>
      
      <p 
        id={`subject-${subject.id}-description`}
        className={`text-sm mb-4 ${subject.locked ? 'text-gray-400' : 'text-gray-600'}`}
      >
        {subject.description}
      </p>
      
      <div className="flex items-center justify-between">
        <div className="text-sm">
          {subject.locked ? (
            <span className="text-gray-500 font-medium">Subscription Required</span>
          ) : (
            <span className="text-primary-600 font-medium">Available</span>
          )}
        </div>
        
        <div className="text-right">
          <div className={`text-sm ${subject.locked ? 'text-gray-400' : 'text-gray-600'}`}>
            From ${subject.pricing?.monthly}/month
          </div>
        </div>
      </div>
    </div>
  );

  const SubjectDropdown = ({ subjects, selectedSubject, onSelect, id }) => (
    <div className="relative">
      <select
        id={id}
        value={selectedSubject?.id || ''}
        onChange={(e) => {
          const subject = subjects.find(s => s.id === e.target.value);
          if (subject && !subject.locked) {
            onSelect(subject);
          }
        }}
        className="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white min-h-[48px]"
        aria-label="Select a programming subject"
      >
        <option value="">Choose a subject...</option>
        {subjects.map((subject) => (
          <option 
            key={subject.id} 
            value={subject.id}
            disabled={subject.locked}
          >
            {subject.name} {subject.locked ? '(Subscription Required)' : ''}
          </option>
        ))}
      </select>
    </div>
  );

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Select a Subject</h2>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" role="progressbar" aria-label="Loading"></div>
          <span className="ml-3 text-gray-600">Loading subjects...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Select a Subject</h2>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <svg
              className="w-5 h-5 text-red-400 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading subjects</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              <button
                onClick={fetchSubjects}
                className="mt-3 text-sm font-medium text-red-800 hover:text-red-900 focus:outline-none focus:underline"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Select a Subject</h2>
        <p className="text-gray-600">
          Choose a programming subject to begin your personalized learning journey.
        </p>
      </div>

      {/* View mode toggle - Hidden on mobile, shows dropdown by default */}
      <div className="hidden tablet:flex justify-between items-center mb-6">
        <div className="text-sm text-gray-600">
          {subjects.length} subjects available
        </div>
        
        <div className="flex rounded-lg border border-gray-300 overflow-hidden">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-4 py-2 text-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              viewMode === 'grid'
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
            aria-pressed={viewMode === 'grid'}
          >
            <svg className="w-4 h-4 mr-2 inline" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
            Grid
          </button>
          <button
            onClick={() => setViewMode('dropdown')}
            className={`px-4 py-2 text-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              viewMode === 'dropdown'
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
            aria-pressed={viewMode === 'dropdown'}
          >
            <svg className="w-4 h-4 mr-2 inline" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
            List
          </button>
        </div>
      </div>

      {/* Mobile: Always show dropdown */}
      <div className="block tablet:hidden mb-6">
        <label htmlFor="mobile-subject-select" className="block text-sm font-medium text-gray-700 mb-2">
          Choose a subject:
        </label>
        <SubjectDropdown
          subjects={subjects}
          selectedSubject={selectedSubject}
          onSelect={handleSubjectSelect}
          id="mobile-subject-select"
        />
      </div>

      {/* Tablet/Desktop: Show based on view mode */}
      <div className="hidden tablet:block">
        {viewMode === 'dropdown' ? (
          <div className="mb-6">
            <label htmlFor="desktop-subject-select" className="block text-sm font-medium text-gray-700 mb-2">
              Choose a subject:
            </label>
            <SubjectDropdown
              subjects={subjects}
              selectedSubject={selectedSubject}
              onSelect={handleSubjectSelect}
              id="desktop-subject-select"
            />
          </div>
        ) : (
          <div className="grid grid-cols-1 tablet:grid-cols-2 desktop:grid-cols-3 gap-6">
            {subjects.map((subject) => (
              <SubjectCard
                key={subject.id}
                subject={subject}
                isSelected={selectedSubject?.id === subject.id}
                onClick={handleSubjectSelect}
              />
            ))}
          </div>
        )}
      </div>

      {/* Selected subject confirmation */}
      {selectedSubject && (
        <div className="mt-8 p-4 bg-primary-50 border border-primary-200 rounded-lg">
          <div className="flex items-start">
            <svg
              className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-primary-800">
                {selectedSubject.name} Selected
              </h3>
              <p className="text-sm text-primary-700 mt-1">
                You can now proceed to take the knowledge assessment survey.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {subjects.length === 0 && (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No subjects available</h3>
          <p className="mt-1 text-sm text-gray-500">
            There are currently no programming subjects available for selection.
          </p>
        </div>
      )}
    </div>
  );
};

export default SubjectSelector;