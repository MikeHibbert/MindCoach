import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const SubjectSelector = ({ onSubjectSelect }) => {
  const { user, authenticatedFetch } = useAuth();
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSubject, setNewSubject] = useState({ name: '', description: '' });
  const [addingSubject, setAddingSubject] = useState(false);
  const navigate = useNavigate();
  
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

  const fetchSubjects = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const url = user 
        ? `${API_BASE_URL}/subjects?user_id=${encodeURIComponent(user.user_id)}`
        : `${API_BASE_URL}/subjects`;
      
      const response = user 
        ? await authenticatedFetch(url)
        : await fetch(url);
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
  }, [user, authenticatedFetch]);

  // Fetch subjects on component mount
  useEffect(() => {
    fetchSubjects();
  }, [fetchSubjects]);

  const handleSubjectSelect = async (subject) => {
    setSelectedSubject(subject);
    setLoading(true);
    
    // Determine user ID for API calls
    const effectiveUserId = user ? user.user_id : 'anonymous';
    
    try {
      // Check if lessons already exist for this subject
      const lessonsResponse = user 
        ? await authenticatedFetch(`${API_BASE_URL}/users/${effectiveUserId}/subjects/${subject.id}/lessons`)
        : await fetch(`${API_BASE_URL}/users/${effectiveUserId}/subjects/${subject.id}/lessons`);
      
      if (lessonsResponse.ok) {
        const lessonsData = await lessonsResponse.json();
        
        // If lessons exist and there are actual lessons available, go to lessons
        if (lessonsData.success && lessonsData.lessons && lessonsData.lessons.length > 0) {
          const lessonsPath = user 
            ? `/users/${user.user_id}/subjects/${subject.id}/lessons`
            : `/subjects/${subject.id}/lessons`;
          
          console.log('Lessons found, navigating to:', lessonsPath);
          navigate(lessonsPath);
          
          if (onSubjectSelect) {
            onSubjectSelect(subject);
          }
          return;
        }
      }
      
      // Check if survey results exist
      const surveyResponse = user 
        ? await authenticatedFetch(`${API_BASE_URL}/users/${effectiveUserId}/subjects/${subject.id}/survey/results`)
        : await fetch(`${API_BASE_URL}/users/${effectiveUserId}/subjects/${subject.id}/survey/results`);
      
      if (surveyResponse.ok) {
        const surveyData = await surveyResponse.json();
        
        // If survey results exist, go to results page
        if (surveyData.success && surveyData.results) {
          const resultsPath = user 
            ? `/users/${user.user_id}/subjects/${subject.id}/results`
            : `/subjects/${subject.id}/results`;
          
          console.log('Survey results found, navigating to:', resultsPath);
          navigate(resultsPath);
          
          if (onSubjectSelect) {
            onSubjectSelect(subject);
          }
          return;
        }
      }
    } catch (error) {
      console.log('Error checking existing data, proceeding to survey:', error);
    } finally {
      setLoading(false);
    }
    
    // Default: Navigate to survey (first time or if checks failed)
    const surveyPath = user 
      ? `/users/${user.user_id}/subjects/${subject.id}/survey`
      : `/subjects/${subject.id}/survey`;
    
    console.log('No existing data found, navigating to survey:', surveyPath);
    navigate(surveyPath);
    
    if (onSubjectSelect) {
      onSubjectSelect(subject);
    }
  };

  const handleAddSubject = async (e) => {
    e.preventDefault();
    if (!newSubject.name.trim() || !newSubject.description.trim()) {
      setError('Please fill in both name and description');
      return;
    }

    try {
      setAddingSubject(true);
      setError(null);

      const response = user 
        ? await authenticatedFetch(`${API_BASE_URL}/subjects`, {
            method: 'POST',
            body: JSON.stringify(newSubject)
          })
        : await fetch(`${API_BASE_URL}/subjects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newSubject)
          });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to add subject');
      }

      // Add the new subject to the list
      setSubjects(prev => [...prev, data.subject]);
      setNewSubject({ name: '', description: '' });
      setShowAddForm(false);
      
    } catch (err) {
      console.error('Error adding subject:', err);
      setError(err.message);
    } finally {
      setAddingSubject(false);
    }
  };



  const SubjectCard = ({ subject, isSelected, onClick }) => {
    return (
      <div
        className={`
          relative p-6 rounded-lg border-2 transition-all duration-200 cursor-pointer
          ${isSelected
            ? 'border-blue-600 bg-blue-50 shadow-md'
            : 'border-gray-300 bg-white hover:border-blue-400 hover:shadow-sm'
          }
          focus:outline-none focus:ring-3 focus:ring-blue-500 focus:ring-offset-2
        `}
        onClick={() => onClick(subject)}
        tabIndex={0}
        role="button"
        aria-pressed={isSelected}
        data-testid={`subject-card-${subject.id}`}
      >
        {/* Selection indicator */}
        {isSelected && (
          <div className="absolute top-3 right-3" aria-hidden="true">
            <svg
              className="w-6 h-6 text-blue-700"
              fill="currentColor"
              viewBox="0 0 20 20"
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
          <h3 className="text-lg font-semibold text-gray-900">
            {subject.name}
          </h3>
        </div>
        
        <p className="text-sm mb-4 text-gray-700">
          {subject.description}
        </p>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading subjects</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
            <div className="mt-4">
              <button
                onClick={fetchSubjects}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose Your Subject</h2>
          <p className="text-gray-600">Select a subject to start your personalized learning journey.</p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Subject
        </button>
      </div>

      {/* Add Subject Form */}
      {showAddForm && (
        <div className="bg-white p-6 rounded-lg border-2 border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Subject</h3>
          <form onSubmit={handleAddSubject} className="space-y-4">
            <div>
              <label htmlFor="subject-name" className="block text-sm font-medium text-gray-700 mb-1">
                Subject Name
              </label>
              <input
                id="subject-name"
                type="text"
                value={newSubject.name}
                onChange={(e) => setNewSubject(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Python Programming"
                required
              />
            </div>
            <div>
              <label htmlFor="subject-description" className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                id="subject-description"
                value={newSubject.description}
                onChange={(e) => setNewSubject(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Brief description of what this subject covers..."
                required
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false);
                  setNewSubject({ name: '', description: '' });
                  setError(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={addingSubject}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {addingSubject ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Adding...
                  </>
                ) : (
                  'Add Subject'
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {subjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {subjects.map((subject) => (
            <SubjectCard
              key={subject.id}
              subject={subject}
              isSelected={selectedSubject?.id === subject.id}
              onClick={handleSubjectSelect}
            />
          ))}
        </div>
      ) : !loading && (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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