import React, { useState, useEffect, useRef } from 'react';
import PipelineService from '../services/pipelineService';
import { 
  announceToScreenReader, 
  focusManagement 
} from '../utils/accessibility';

const PipelineProgressTracker = ({ 
  userId, 
  subject, 
  onComplete, 
  onError,
  autoStart = false,
  className = '' 
}) => {
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [pipelineId, setPipelineId] = useState(null);
  const [error, setError] = useState(null);
  const [isStarting, setIsStarting] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  
  // Refs for accessibility
  const progressRef = useRef(null);
  const errorRef = useRef(null);
  
  const maxRetries = 3;

  useEffect(() => {
    if (autoStart && userId && subject && !pipelineId && !isStarting) {
      startPipeline();
    }
  }, [autoStart, userId, subject, pipelineId, isStarting]);

  const startPipeline = async () => {
    if (isStarting) return;
    
    setIsStarting(true);
    setError(null);
    setPipelineStatus(null);
    
    try {
      const response = await PipelineService.startContentGeneration(userId, subject);
      
      if (response.success) {
        setPipelineId(response.pipeline_id);
        setPipelineStatus({
          status: 'started',
          current_stage: 'initializing',
          progress_percentage: 0,
          message: 'Pipeline started successfully'
        });
        
        announceToScreenReader('Content generation pipeline started', 'polite');
        
        // Start polling for status updates
        PipelineService.pollPipelineStatus(
          userId,
          subject,
          response.pipeline_id,
          handleStatusUpdate,
          handlePipelineComplete,
          handlePipelineError
        );
      } else {
        throw new Error(response.message || 'Failed to start pipeline');
      }
    } catch (err) {
      handlePipelineError(err);
    } finally {
      setIsStarting(false);
    }
  };

  const handleStatusUpdate = (status) => {
    setPipelineStatus(status);
    
    // Announce significant progress updates
    if (status.current_stage) {
      const stageMessages = {
        'curriculum_generation': 'Generating curriculum structure',
        'lesson_planning': 'Creating detailed lesson plans',
        'content_generation': 'Generating lesson content'
      };
      
      const message = stageMessages[status.current_stage] || `Stage: ${status.current_stage}`;
      announceToScreenReader(message, 'polite');
    }
  };

  const handlePipelineComplete = (status) => {
    setPipelineStatus({
      ...status,
      status: 'completed',
      progress_percentage: 100
    });
    
    announceToScreenReader('Content generation completed successfully!', 'assertive');
    
    if (onComplete) {
      onComplete(status);
    }
  };

  const handlePipelineError = (err) => {
    console.error('Pipeline error:', err);
    setError(err);
    setPipelineStatus(null);
    
    announceToScreenReader(`Error: ${err.message}`, 'assertive');
    
    // Focus error message for screen readers
    if (errorRef.current) {
      focusManagement.setFocus(errorRef.current, 100);
    }
    
    if (onError) {
      onError(err);
    }
  };

  const retryPipeline = () => {
    if (retryCount < maxRetries) {
      setRetryCount(prev => prev + 1);
      setError(null);
      setPipelineId(null);
      startPipeline();
    }
  };

  const getProgressPercentage = () => {
    if (!pipelineStatus) return 0;
    
    if (pipelineStatus.progress_percentage !== undefined) {
      return pipelineStatus.progress_percentage;
    }
    
    // Calculate progress based on stage
    const stageProgress = {
      'initializing': 5,
      'curriculum_generation': 20,
      'lesson_planning': 50,
      'content_generation': 80,
      'completed': 100
    };
    
    return stageProgress[pipelineStatus.current_stage] || 0;
  };

  const getStageDisplayName = (stage) => {
    const stageNames = {
      'initializing': 'Initializing',
      'curriculum_generation': 'Curriculum Generation',
      'lesson_planning': 'Lesson Planning',
      'content_generation': 'Content Generation',
      'completed': 'Completed'
    };
    
    return stageNames[stage] || stage;
  };

  const renderProgressIndicator = () => {
    const progressPercentage = getProgressPercentage();
    const currentStage = pipelineStatus?.current_stage || 'initializing';
    
    return (
      <div 
        ref={progressRef}
        className="pipeline-progress bg-white border-2 border-gray-200 rounded-lg p-6"
        role="region"
        aria-label="Content generation progress"
        aria-live="polite"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Generating Learning Content
          </h3>
          <span className="text-sm text-gray-600 font-medium">
            {Math.round(progressPercentage)}%
          </span>
        </div>
        
        {/* Progress Bar */}
        <div 
          className="w-full bg-gray-200 rounded-full h-4 border border-gray-300 mb-4"
          role="progressbar"
          aria-valuenow={Math.round(progressPercentage)}
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label={`Content generation progress: ${Math.round(progressPercentage)}% complete`}
        >
          <div
            className="bg-blue-600 h-full rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        
        {/* Stage Indicators */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {['curriculum_generation', 'lesson_planning', 'content_generation'].map((stage, index) => {
            const isActive = currentStage === stage;
            const isCompleted = getStageOrder(currentStage) > getStageOrder(stage);
            
            return (
              <div
                key={stage}
                className={`flex items-center p-3 rounded-lg border-2 transition-colors ${
                  isActive
                    ? 'bg-blue-50 border-blue-300 text-blue-900'
                    : isCompleted
                    ? 'bg-green-50 border-green-300 text-green-800'
                    : 'bg-gray-50 border-gray-200 text-gray-600'
                }`}
              >
                <div 
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3 ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : isCompleted
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-400 text-gray-100'
                  }`}
                  aria-hidden="true"
                >
                  {isCompleted ? '✓' : index + 1}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-sm">
                    {getStageDisplayName(stage)}
                  </div>
                  {isActive && (
                    <div className="text-xs opacity-75">
                      In progress...
                    </div>
                  )}
                  {isCompleted && (
                    <div className="text-xs opacity-75">
                      Completed
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Current Status Message */}
        {pipelineStatus?.message && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-blue-800 text-sm">
              {pipelineStatus.message}
            </p>
          </div>
        )}
        
        {/* Lesson Generation Progress */}
        {pipelineStatus?.lessons_completed !== undefined && pipelineStatus?.total_lessons && (
          <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="flex justify-between text-sm text-gray-700 mb-2">
              <span>Lessons Generated</span>
              <span>{pipelineStatus.lessons_completed} / {pipelineStatus.total_lessons}</span>
            </div>
            <div 
              className="w-full bg-gray-200 rounded-full h-2"
              role="progressbar"
              aria-valuenow={pipelineStatus.lessons_completed}
              aria-valuemin="0"
              aria-valuemax={pipelineStatus.total_lessons}
              aria-label={`Lessons generated: ${pipelineStatus.lessons_completed} of ${pipelineStatus.total_lessons}`}
            >
              <div
                className="bg-green-600 h-full rounded-full transition-all duration-300"
                style={{ 
                  width: `${(pipelineStatus.lessons_completed / pipelineStatus.total_lessons) * 100}%` 
                }}
              />
            </div>
          </div>
        )}
      </div>
    );
  };

  const getStageOrder = (stage) => {
    const stageOrder = {
      'initializing': 0,
      'curriculum_generation': 1,
      'lesson_planning': 2,
      'content_generation': 3,
      'completed': 4
    };
    return stageOrder[stage] || 0;
  };

  const renderError = () => (
    <div 
      ref={errorRef}
      className="pipeline-error bg-red-50 border-2 border-red-200 rounded-lg p-6"
      role="alert"
      aria-live="assertive"
      tabIndex="-1"
    >
      <div className="flex items-start">
        <svg 
          className="w-6 h-6 text-red-500 mr-3 mt-0.5 flex-shrink-0" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
          />
        </svg>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-red-900 mb-2">
            Content Generation Failed
          </h3>
          <p className="text-red-800 mb-4">
            {error.message || 'An unexpected error occurred during content generation.'}
          </p>
          
          {error.type === 'subscription_required' && (
            <div className="bg-red-100 border border-red-300 rounded-lg p-3 mb-4">
              <p className="text-red-800 text-sm">
                You need an active subscription to generate content for this subject.
              </p>
            </div>
          )}
          
          {error.type === 'prerequisite_missing' && (
            <div className="bg-red-100 border border-red-300 rounded-lg p-3 mb-4">
              <p className="text-red-800 text-sm">
                Please complete the subject survey before generating lessons.
              </p>
            </div>
          )}
          
          <div className="flex flex-col sm:flex-row gap-3">
            {retryCount < maxRetries && (
              <button
                onClick={retryPipeline}
                className="btn-primary focus:ring-red-500"
                aria-label={`Retry content generation (attempt ${retryCount + 1} of ${maxRetries})`}
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Retry ({retryCount + 1}/{maxRetries})
              </button>
            )}
            
            {retryCount >= maxRetries && (
              <p className="text-red-700 text-sm">
                Maximum retry attempts reached. Please try again later or contact support.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const renderStartButton = () => (
    <div className="pipeline-start bg-white border-2 border-gray-200 rounded-lg p-6 text-center">
      <div className="mb-4">
        <svg 
          className="w-16 h-16 text-blue-500 mx-auto mb-4" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={1.5} 
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" 
          />
        </svg>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Ready to Generate Your Learning Content
        </h3>
        <p className="text-gray-600 mb-6">
          Our AI will create personalized lessons based on your survey results using a 3-stage process:
          curriculum planning, lesson structuring, and content generation.
        </p>
      </div>
      
      <button
        onClick={startPipeline}
        disabled={isStarting}
        className={`btn-primary text-lg px-8 py-3 ${isStarting ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-label="Start content generation pipeline"
      >
        {isStarting ? (
          <>
            <svg className="animate-spin w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Starting Pipeline...
          </>
        ) : (
          <>
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Generate Learning Content
          </>
        )}
      </button>
    </div>
  );

  if (!userId || !subject) {
    return (
      <div className={`pipeline-tracker ${className}`}>
        <div className="text-center text-gray-600 p-6">
          Please select a subject to generate content.
        </div>
      </div>
    );
  }

  return (
    <div className={`pipeline-tracker ${className}`}>
      {error && renderError()}
      {!error && !pipelineStatus && !isStarting && renderStartButton()}
      {(pipelineStatus || isStarting) && !error && renderProgressIndicator()}
    </div>
  );
};

export default PipelineProgressTracker;