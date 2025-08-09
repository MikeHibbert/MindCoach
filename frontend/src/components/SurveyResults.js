import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import SurveyService from '../services/surveyService';

const SurveyResults = () => {
  const { userId, subject } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [results, setResults] = useState(location.state?.surveyResults || null);
  const [isLoading, setIsLoading] = useState(!results);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!results && userId && subject) {
      loadResults();
    }
  }, [userId, subject, results]);

  const loadResults = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const surveyResults = await SurveyService.getSurveyResults(userId, subject);
      setResults(surveyResults);
    } catch (err) {
      console.error('Error loading survey results:', err);
      setError(err.message || 'Failed to load survey results');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartLearning = () => {
    navigate(`/users/${userId}/subjects/${subject}/lessons`);
  };

  const handleRetakeSurvey = () => {
    navigate(`/users/${userId}/subjects/${subject}/survey`);
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <span className="ml-3 text-gray-600">Loading results...</span>
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
            <p className="text-gray-600 mb-4">{error}</p>
            <button 
              onClick={loadResults}
              className="btn-primary"
            >
              Retry
            </button>
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
            <p className="text-gray-600 mb-4">No survey results found.</p>
            <button 
              onClick={handleRetakeSurvey}
              className="btn-primary"
            >
              Take Survey
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
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Assessment Complete! 🎉
        </h1>
        <p className="text-lg text-gray-600">
          Here are your {results.subject} assessment results
        </p>
      </div>

      {/* Main Results Card */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Skill Level */}
          <div className="text-center">
            <div className="mb-3">
              <span className={`inline-flex items-center px-4 py-2 rounded-full text-lg font-semibold border-2 ${getSkillLevelColor(results.skill_level)}`}>
                {results.skill_level?.charAt(0).toUpperCase() + results.skill_level?.slice(1) || 'Unknown'}
              </span>
            </div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              Skill Level
            </h3>
          </div>

          {/* Accuracy */}
          <div className="text-center">
            <div className={`text-4xl font-bold mb-2 ${getAccuracyColor(results.accuracy)}`}>
              {Math.round(results.accuracy)}%
            </div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              Accuracy
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {results.correct_answers} of {results.total_questions} correct
            </p>
          </div>

          {/* Score */}
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600 mb-2">
              {results.correct_answers}/{results.total_questions}
            </div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              Score
            </h3>
          </div>
        </div>

        {/* Topic Analysis */}
        {results.topic_analysis && Object.keys(results.topic_analysis).length > 0 && (
          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Topic Breakdown
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(results.topic_analysis).map(([topic, analysis]) => (
                <div key={topic} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900 capitalize">
                      {topic.replace(/_/g, ' ')}
                    </h4>
                    <span className={`text-sm font-semibold ${getAccuracyColor(analysis.accuracy)}`}>
                      {Math.round(analysis.accuracy)}%
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    {analysis.correct} of {analysis.total} questions correct
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div
                      className={`h-2 rounded-full ${
                        analysis.accuracy >= 80 ? 'bg-green-500' :
                        analysis.accuracy >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${analysis.accuracy}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {results.recommendations && results.recommendations.length > 0 && (
          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Personalized Recommendations
            </h3>
            <div className="space-y-3">
              {results.recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start">
                  <div className="flex-shrink-0 w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-primary-600 text-sm font-medium">
                      {index + 1}
                    </span>
                  </div>
                  <p className="text-gray-700">{recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          onClick={handleStartLearning}
          className="btn-primary px-8 py-3 text-lg"
        >
          Start Learning Path
        </button>
        <button
          onClick={handleRetakeSurvey}
          className="btn-secondary px-8 py-3 text-lg"
        >
          Retake Assessment
        </button>
      </div>

      {/* Additional Info */}
      <div className="text-center text-sm text-gray-500">
        <p>
          Assessment completed on {new Date(results.processed_at).toLocaleDateString()}
        </p>
        <p className="mt-1">
          Your personalized learning path will be generated based on these results.
        </p>
      </div>

      {/* Debug Info (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="bg-gray-100 rounded-lg p-4">
          <details>
            <summary className="cursor-pointer text-sm font-medium text-gray-700">
              Debug Info (Development Only)
            </summary>
            <pre className="mt-4 text-xs bg-white p-4 rounded border overflow-auto">
              {JSON.stringify(results, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
};

export default SurveyResults;