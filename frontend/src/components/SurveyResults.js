import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import SurveyService from '../services/surveyService';

const SurveyResults = () => {
  const { userId, subject } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get results from navigation state or fetch from API
  useEffect(() => {
    console.log('SurveyResults params:', { userId, subject });
    console.log('Current location:', location.pathname);
    
    const loadResults = async () => {
      try {
        setLoading(true);
        setError(null);

        // First try to get results from navigation state
        const stateResults = location.state?.surveyResults;
        if (stateResults) {
          console.log('Using results from navigation state:', stateResults);
          setResults(stateResults);
          setLoading(false);
          return;
        }

        // If no state results, try to fetch from API
        const effectiveUserId = userId || 'anonymous';
        console.log('Fetching results from API for:', effectiveUserId, subject);
        
        const apiResults = await SurveyService.getSurveyResults(effectiveUserId, subject);
        setResults(apiResults);
        
      } catch (err) {
        console.error('Error loading survey results:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (subject) {
      loadResults();
    } else {
      setError('Missing subject parameter');
      setLoading(false);
    }
  }, [userId, subject, location.state]);

  const handleStartLearning = () => {
    // Determine the correct path based on current route structure
    const effectiveUserId = userId || 'anonymous';
    const lessonsPath = `/users/${effectiveUserId}/subjects/${subject}/lessons`;
    
    console.log('Navigating to lessons:', lessonsPath);
    navigate(lessonsPath);
  };

  const handleRetakeAssessment = () => {
    const surveyPath = userId 
      ? `/users/${userId}/subjects/${subject}/survey`
      : `/subjects/${subject}/survey`;
    navigate(surveyPath);
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading your results...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card">
          <div className="text-center py-8">
            <div className="text-red-500 text-lg mb-4">⚠️ Error Loading Results</div>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="flex justify-center space-x-4">
              <button 
                onClick={() => window.location.reload()}
                className="btn-primary"
              >
                Retry
              </button>
              <button 
                onClick={() => navigate('/')}
                className="btn-secondary"
              >
                Back to Home
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card">
          <div className="text-center py-8">
            <div className="text-gray-500 text-lg mb-4">📊 No Results Available</div>
            <p className="text-gray-600 mb-6">
              We couldn't find your assessment results. Please retake the assessment.
            </p>
            <button 
              onClick={handleRetakeAssessment}
              className="btn-primary"
            >
              Take Assessment
            </button>
          </div>
        </div>
      </div>
    );
  }

  const getSkillLevelColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'beginner':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'advanced':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 80) return 'text-green-600';
    if (accuracy >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="card">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Assessment Results
          </h1>
          <p className="text-gray-600">
            {results.subject || subject} • Completed {new Date(results.processed_at || Date.now()).toLocaleDateString()}
          </p>
        </div>
      </div>

      {/* Overall Score */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {results.accuracy || 0}%
            </div>
            <div className="text-sm text-gray-600">Overall Score</div>
          </div>
          <div className="text-center">
            <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium border ${getSkillLevelColor(results.skill_level)}`}>
              {results.skill_level || 'Unknown'}
            </div>
            <div className="text-sm text-gray-600 mt-2">Skill Level</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {results.correct_answers || 0}/{results.total_questions || 0}
            </div>
            <div className="text-sm text-gray-600">Correct Answers</div>
          </div>
        </div>
      </div>

      {/* Topic Analysis */}
      {results.topic_analysis && Object.keys(results.topic_analysis).length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Topic Performance</h2>
          <div className="space-y-4">
            {Object.entries(results.topic_analysis).map(([topic, analysis]) => (
              <div key={topic} className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-medium text-gray-900 capitalize">
                    {topic.replace(/_/g, ' ')}
                  </h3>
                  <span className={`font-semibold ${getAccuracyColor(analysis.accuracy || 0)}`}>
                    {analysis.accuracy || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${analysis.accuracy || 0}%` }}
                  />
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  {analysis.correct || 0} of {analysis.total || 0} questions correct
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {results.recommendations && results.recommendations.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Personalized Recommendations</h2>
          <div className="space-y-3">
            {results.recommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 text-sm font-medium">{index + 1}</span>
                </div>
                <p className="text-gray-700">{recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={handleStartLearning}
            className="btn-primary flex items-center justify-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Start Learning Path
          </button>
          <button
            onClick={handleRetakeAssessment}
            className="btn-secondary flex items-center justify-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Retake Assessment
          </button>
        </div>
      </div>

      {/* Debug Info (Development Only) */}
      {process.env.NODE_ENV === 'development' && results && (
        <div className="card">
          <details className="bg-gray-100 rounded-lg p-4">
            <summary className="cursor-pointer text-sm font-medium text-gray-700">
              Debug Info (Development Only)
            </summary>
            <div className="mt-4 text-xs">
              <pre className="whitespace-pre-wrap text-gray-600">
                {JSON.stringify(results, null, 2)}
              </pre>
            </div>
          </details>
        </div>
      )}
    </div>
  );
};

export default SurveyResults;