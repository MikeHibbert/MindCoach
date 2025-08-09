import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Survey from './Survey';
import SurveyService from '../services/surveyService';

const SurveyContainer = () => {
  const { userId, subject } = useParams();
  const navigate = useNavigate();
  
  const [surveyData, setSurveyData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [progress, setProgress] = useState({
    currentQuestion: 1,
    totalQuestions: 0,
    answeredQuestions: 0,
    progressPercentage: 0
  });

  // Load survey data on component mount
  useEffect(() => {
    loadSurvey();
  }, [userId, subject]);

  const loadSurvey = async (forceGenerate = false) => {
    if (!userId || !subject) {
      setError('Missing user ID or subject parameter');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const survey = await SurveyService.getOrGenerateSurvey(
        userId, 
        subject, 
        forceGenerate
      );

      // Validate survey data
      if (!SurveyService.validateSurveyData(survey)) {
        throw new Error('Invalid survey data received from server');
      }

      setSurveyData(survey);
    } catch (err) {
      console.error('Error loading survey:', err);
      setError(err.message || 'Failed to load survey');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSurveySubmit = async (submissionData) => {
    if (!userId || !subject) {
      throw new Error('Missing user ID or subject');
    }

    try {
      setIsSubmitting(true);
      setError(null);

      // Submit survey answers
      const results = await SurveyService.submitSurvey(
        userId,
        subject,
        submissionData
      );

      // Handle successful submission
      console.log('Survey submitted successfully:', results);
      
      // Navigate to results page or next step
      navigate(`/users/${userId}/subjects/${subject}/results`, {
        state: { 
          surveyResults: results,
          subject: subject,
          userId: userId
        }
      });

    } catch (err) {
      console.error('Error submitting survey:', err);
      setError(err.message || 'Failed to submit survey');
      throw err; // Re-throw to let Survey component handle UI state
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleProgress = useCallback((progressData) => {
    setProgress(progressData);
  }, []);

  const handleRetry = () => {
    setError(null);
    loadSurvey(false);
  };

  const handleRegenerateSurvey = () => {
    loadSurvey(true);
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <span className="ml-3 text-gray-600">Loading survey...</span>
          </div>
        </div>
      </div>
    );
  }

  // Show error state with retry options
  if (error && !surveyData) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card">
          <div className="text-center py-8">
            <div className="text-red-500 text-lg mb-4">⚠️ Error Loading Survey</div>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="flex justify-center space-x-4">
              <button 
                onClick={handleRetry}
                className="btn-primary"
              >
                Retry
              </button>
              <button 
                onClick={handleRegenerateSurvey}
                className="btn-secondary"
              >
                Generate New Survey
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Progress Summary */}
      {surveyData && (
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  {surveyData.subject_name || surveyData.subject} Assessment
                </h1>
                <p className="text-sm text-gray-600">
                  Question {progress.currentQuestion} of {progress.totalQuestions} • {progress.answeredQuestions} answered
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-primary-600">
                  {progress.progressPercentage}%
                </div>
                <div className="text-xs text-gray-500">Complete</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Survey Component */}
      <Survey
        surveyData={surveyData}
        onSubmit={handleSurveySubmit}
        onProgress={handleProgress}
        isLoading={isSubmitting}
        error={error}
      />

      {/* Survey Actions */}
      {surveyData && (
        <div className="max-w-4xl mx-auto">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                <p>Having trouble with the survey?</p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleRegenerateSurvey}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                  disabled={isLoading || isSubmitting}
                >
                  Generate New Survey
                </button>
                <button
                  onClick={() => navigate(-1)}
                  className="text-sm text-gray-600 hover:text-gray-700 font-medium"
                  disabled={isSubmitting}
                >
                  Go Back
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Debug Info (only in development) */}
      {process.env.NODE_ENV === 'development' && surveyData && (
        <div className="max-w-4xl mx-auto">
          <details className="bg-gray-100 rounded-lg p-4">
            <summary className="cursor-pointer text-sm font-medium text-gray-700">
              Debug Info (Development Only)
            </summary>
            <div className="mt-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <strong>Survey ID:</strong> {surveyData.id || 'N/A'}
                </div>
                <div>
                  <strong>User ID:</strong> {surveyData.user_id}
                </div>
                <div>
                  <strong>Subject:</strong> {surveyData.subject}
                </div>
                <div>
                  <strong>Questions:</strong> {surveyData.questions?.length || 0}
                </div>
                <div>
                  <strong>Generated:</strong> {surveyData.generated_at || 'N/A'}
                </div>
                <div>
                  <strong>Topics:</strong> {surveyData.metadata?.topics_covered?.join(', ') || 'N/A'}
                </div>
              </div>
            </div>
          </details>
        </div>
      )}
    </div>
  );
};

export default SurveyContainer;