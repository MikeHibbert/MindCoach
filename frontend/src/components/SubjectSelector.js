import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import AddSubjectModal from './AddSubjectModal';

const SubjectSelector = ({ onSubjectSelect }) => {
  const { user, authenticatedFetch } = useAuth();
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddSubjectModal, setShowAddSubjectModal] = useState(false);
  const [userTokens, setUserTokens] = useState(0);
  const [isCreatingSubject, setIsCreatingSubject] = useState(false);
  const navigate = useNavigate();

  // Fetch subjects and user tokens on component mount
  useEffect(() => {
    fetchSubjects();
    if (user) {
      fetchUserTokens();
    }
  }, [user]);

  const fetchSubjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';
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
  };

  const fetchUserTokens = async () => {
    try {
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';
      const response = await authenticatedFetch(`${API_BASE_URL}/users/${encodeURIComponent(user.user_id)}/tokens`);
      const data = await response.json();
      
      if (response.ok) {
        setUserTokens(data.tokens || 0);
      }
    } catch (err) {
      console.error('Error fetching user tokens:', err);
      // Don't show error for tokens, just default to 0
    }
  };

  const handleCreateCustomSubject = async (subjectData) => {
    try {
      setIsCreatingSubject(true);
      setError(null);
      
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';
      const response = await authenticatedFetch(`${API_BASE_URL}/users/${encodeURIComponent(user.user_id)}/subjects/custom`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(subjectData),
      });

      const data = await response.json();
      
      if (!response.ok) {
        if (response.status === 402) {
          throw new Error('Insufficient tokens to create custom subject');
        }
        throw new Error(data.error?.message || 'Failed to create custom subject');
      }

      // Refresh subjects list and user tokens
      await fetchSubjects();
      await fetchUserTokens();
      
      setShowAddSubjectModal(false);
      
      // Navigate to the newly created subject
      navigate(`/subjects/${data.subject.id}/survey`);
      
    } catch (err) {
      console.error('Error creating custom subject:', err);
      setError(err.message);
    } finally {
      setIsCreatingSubject(false);
    }
  };

  const handleSubjectSelect = async (subject) => {
    if (subject.locked) {
      return;
    }

    try {
      setError(null);
      setSelectedSubject(subject);
      
      // Persist subject selection to backend if user is authenticated
      if (user) {
        const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';
        const response = await authenticatedFetch(`${API_BASE_URL}/users/${encodeURIComponent(user.user_id)}/subjects/${encodeURIComponent(subject.id)}/select`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          const errorData = await response.json();
          
          if (response.status === 402) {
            const errorMessage = `Subscription required for ${subject.name}`;
            setError(errorMessage);
            setSelectedSubject(null);
            return;
          }
          
          throw new Error(errorData.error?.message || 'Failed to select subject');
        }

        const data = await response.json();
        console.log('Subject selection saved:', data);
      }
      
      // Call parent callback if provided
      if (onSubjectSelect) {
        onSubjectSelect(subject);
      }
      
      // Navigate to the survey page for the selected subject
      // In a real app, you might want to check if the user needs to take a survey first
      // For now, let's navigate to the survey page
      navigate(`/subjects/${subject.id}/survey`);
    } catch (err) {
      console.error('Error selecting subject:', err);
      const errorMessage = err.message || 'Failed to select subject';
      setError(errorMessage);
      setSelectedSubject(null);
    }
  };

  const AddSubjectModal = ({ isOpen, onClose, onSubmit, isLoading, userTokens }) => {
    const [subjectName, setSubjectName] = useState('');
    const [subjectDescription, setSubjectDescription] = useState('');
    const [difficulty, setDifficulty] = useState('beginner');
    const [estimatedLessons, setEstimatedLessons] = useState(10);
    
    const TOKENS_REQUIRED = 50; // Cost to create a custom subject
    const hasEnoughTokens = userTokens >= TOKENS_REQUIRED;

    const handleSubmit = (e) => {
      e.preventDefault();
      if (!subjectName.trim() || !hasEnoughTokens) return;
      
      onSubmit({
        name: subjectName.trim(),
        description: subjectDescription.trim() || `Learn ${subjectName.trim()} programming`,
        difficulty,
        estimatedLessons,
        tokensRequired: TOKENS_REQUIRED
      });
    };

    const resetForm = () => {
      setSubjectName('');
      setSubjectDescription('');
      setDifficulty('beginner');
      setEstimatedLessons(10);
    };

    const handleClose = () => {
      resetForm();
      onClose();
    };

    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg max-w-md w-full p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Create Custom Subject</h3>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600"
              disabled={isLoading}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-800">Your Tokens: {userTokens}</span>
              <span className="text-sm text-blue-600">Cost: {TOKENS_REQUIRED} tokens</span>
            </div>
            {!hasEnoughTokens && (
              <p className="text-sm text-red-600 mt-1">
                Insufficient tokens. You need {TOKENS_REQUIRED - userTokens} more tokens.
              </p>
            )}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="subjectName" className="block text-sm font-medium text-gray-700 mb-1">
                Subject Name *
              </label>
              <input
                id="subjectName"
                type="text"
                value={subjectName}
                onChange={(e) => setSubjectName(e.target.value)}
                placeholder="e.g., Rust Programming, Machine Learning, etc."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="subjectDescription" className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                id="subjectDescription"
                value={subjectDescription}
                onChange={(e) => setSubjectDescription(e.target.value)}
                placeholder="Brief description of what you want to learn..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700 mb-1">
                Starting Difficulty Level
              </label>
              <select
                id="difficulty"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            <div>
              <label htmlFor="estimatedLessons" className="block text-sm font-medium text-gray-700 mb-1">
                Estimated Number of Lessons
              </label>
              <select
                id="estimatedLessons"
                value={estimatedLessons}
                onChange={(e) => setEstimatedLessons(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              >
                <option value={5}>5 lessons (Quick overview)</option>
                <option value={10}>10 lessons (Standard course)</option>
                <option value={15}>15 lessons (Comprehensive)</option>
                <option value={20}>20 lessons (In-depth mastery)</option>
              </select>
            </div>

            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!subjectName.trim() || !hasEnoughTokens || isLoading}
                className={`flex-1 px-4 py-2 rounded-lg transition-colors ${
                  !subjectName.trim() || !hasEnoughTokens || isLoading
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Creating...
                  </div>
                ) : (
                  `Create Subject (${TOKENS_REQUIRED} tokens)`
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const SubjectCard = ({ subject, isSelected, onClick }) => {
    return (
      <div
        className={`
          relative p-6 rounded-lg border-2 transition-all duration-200 cursor-pointer
          ${subject.locked 
            ? 'border-gray-400 bg-gray-100 cursor-not-allowed opacity-70' 
            : isSelected
              ? 'border-blue-600 bg-blue-50 shadow-md'
              : 'border-gray-300 bg-white hover:border-blue-400 hover:shadow-sm'
          }
        `}
        onClick={() => !subject.locked && onClick(subject)}
        role="button"
        tabIndex={subject.locked ? -1 : 0}
      >
        {subject.locked && (
          <div className="absolute top-2 right-2">
            <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
            </svg>
          </div>
        )}
        
        <div className="flex items-center space-x-3">
          <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${subject.color || 'bg-blue-100'}`}>
            <span className="text-2xl">{subject.icon || '📚'}</span>
          </div>
          <div className="flex-1">
            <h3 className={`text-lg font-semibold ${subject.locked ? 'text-gray-500' : 'text-gray-900'}`}>
              {subject.name}
            </h3>
            <p className={`text-sm ${subject.locked ? 'text-gray-400' : 'text-gray-600'}`}>
              {subject.description}
            </p>
          </div>
        </div>

        {subject.locked && (
          <div className="mt-3 text-xs text-gray-500">
            Subscription required
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading subjects...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading subjects</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
            <button
              onClick={fetchSubjects}
              className="mt-2 text-sm text-red-800 underline hover:text-red-900"
            >
              Try again
            </button>
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
          <p className="text-gray-600">Select a programming subject to start your personalized learning journey.</p>
        </div>
        
        {user && (
          <div className="flex flex-col items-end space-y-2">
            <div className="text-sm text-gray-600">
              Tokens: <span className="font-semibold text-blue-600">{userTokens}</span>
            </div>
            <button
              onClick={() => setShowAddSubjectModal(true)}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Custom Subject
            </button>
          </div>
        )}
      </div>

      {subjects.length > 0 ? (
        <div>
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
          
          {/* Add Custom Subject Button */}
          <div className="mt-8 text-center">
            <button
              onClick={() => setShowAddSubjectModal(true)}
              className="inline-flex items-center px-6 py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors duration-200 focus:outline-none focus:ring-3 focus:ring-blue-500 focus:ring-offset-2"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Custom Subject
            </button>
          </div>
        </div>
      ) : (
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

      {/* Add Subject Modal */}
      <AddSubjectModal
        isOpen={showAddSubjectModal}
        onClose={() => setShowAddSubjectModal(false)}
        onSubmit={handleCreateCustomSubject}
        isLoading={isCreatingSubject}
        userTokens={userTokens}
      />
    </div>
  );
};

export default SubjectSelector;