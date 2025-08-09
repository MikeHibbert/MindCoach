import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { 
  announceToScreenReader, 
  keyboardNavigation, 
  ariaLabels, 
  formAccessibility,
  focusManagement 
} from '../utils/accessibility';

const Survey = ({ 
  surveyData, 
  onSubmit, 
  onProgress,
  isLoading = false,
  error = null,
  className = ''
}) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Refs for accessibility
  const questionRef = useRef(null);
  const errorRef = useRef(null);
  const progressRef = useRef(null);
  const optionRefs = useRef([]);

  // Reset state when survey data changes
  useEffect(() => {
    if (surveyData) {
      setCurrentQuestionIndex(0);
      setAnswers({});
      setValidationErrors({});
      announceToScreenReader(`Survey loaded with ${surveyData.questions?.length || 0} questions`);
    }
  }, [surveyData]);

  // Focus management when question changes
  useEffect(() => {
    if (questionRef.current) {
      focusManagement.setFocus(questionRef.current, 100);
    }
  }, [currentQuestionIndex]);

  // Report progress to parent component
  useEffect(() => {
    if (surveyData && onProgress) {
      const totalQuestions = surveyData.questions?.length || 0;
      const answeredQuestions = Object.keys(answers).length;
      const progressPercentage = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;
      
      onProgress({
        currentQuestion: currentQuestionIndex + 1,
        totalQuestions,
        answeredQuestions,
        progressPercentage: Math.round(progressPercentage)
      });
    }
  }, [currentQuestionIndex, answers, surveyData, onProgress]);

  if (isLoading) {
    return (
      <div className={`max-w-4xl mx-auto ${className}`}>
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" role="status" aria-label="Loading"></div>
            <span className="ml-3 text-gray-600">Loading survey...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`max-w-4xl mx-auto ${className}`}>
        <div className="card">
          <div className="text-center py-8">
            <div className="text-red-500 text-lg mb-4">⚠️ Error Loading Survey</div>
            <p className="text-gray-600 mb-4">{error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="btn-primary"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!surveyData || !surveyData.questions || surveyData.questions.length === 0) {
    return (
      <div className={`max-w-4xl mx-auto ${className}`}>
        <div className="card">
          <div className="text-center py-8">
            <div className="text-gray-500 text-lg mb-4">📝 No Survey Available</div>
            <p className="text-gray-600">Please generate a survey first.</p>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = surveyData.questions[currentQuestionIndex];
  const totalQuestions = surveyData.questions.length;
  const isLastQuestion = currentQuestionIndex === totalQuestions - 1;
  const isFirstQuestion = currentQuestionIndex === 0;
  const progressPercentage = ((currentQuestionIndex + 1) / totalQuestions) * 100;

  const handleAnswerChange = (questionId, answer) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
    
    // Clear validation error for this question
    if (validationErrors[questionId]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[questionId];
        return newErrors;
      });
      announceToScreenReader('Answer updated');
    }
  };

  const validateCurrentQuestion = () => {
    const questionId = currentQuestion.id;
    const answer = answers[questionId];
    
    if (answer === undefined || answer === null || answer === '') {
      setValidationErrors(prev => ({
        ...prev,
        [questionId]: 'Please select an answer before continuing.'
      }));
      return false;
    }
    
    return true;
  };

  const handleNext = () => {
    if (!validateCurrentQuestion()) {
      announceToScreenReader('Please answer the current question before continuing', 'assertive');
      return;
    }
    
    if (currentQuestionIndex < totalQuestions - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      announceToScreenReader(`Moving to question ${currentQuestionIndex + 2} of ${totalQuestions}`);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      announceToScreenReader(`Moving to question ${currentQuestionIndex} of ${totalQuestions}`);
    }
  };

  // Handle keyboard navigation for options
  const handleOptionKeyDown = (e, optionIndex, totalOptions, onSelect) => {
    keyboardNavigation.handleArrowKeys(
      e,
      Array(totalOptions).fill(null),
      optionIndex,
      (newIndex) => {
        optionRefs.current[newIndex]?.focus();
      }
    );

    keyboardNavigation.handleActivation(e, () => {
      onSelect();
    });
  };

  const handleSubmit = async () => {
    // Validate all questions are answered
    const unansweredQuestions = surveyData.questions.filter(
      question => answers[question.id] === undefined || answers[question.id] === null || answers[question.id] === ''
    );

    if (unansweredQuestions.length > 0) {
      const newErrors = {};
      unansweredQuestions.forEach(question => {
        newErrors[question.id] = 'This question is required.';
      });
      setValidationErrors(newErrors);
      
      // Navigate to first unanswered question
      const firstUnansweredIndex = surveyData.questions.findIndex(
        question => answers[question.id] === undefined || answers[question.id] === null || answers[question.id] === ''
      );
      if (firstUnansweredIndex !== -1) {
        setCurrentQuestionIndex(firstUnansweredIndex);
      }
      return;
    }

    setIsSubmitting(true);
    
    try {
      // Format answers for submission
      const formattedAnswers = surveyData.questions.map(question => ({
        question_id: question.id,
        answer: answers[question.id],
        question_text: question.question,
        question_type: question.type,
        difficulty: question.difficulty,
        topic: question.topic
      }));

      await onSubmit({
        survey_id: surveyData.id,
        user_id: surveyData.user_id,
        subject: surveyData.subject,
        answers: formattedAnswers,
        completed_at: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error submitting survey:', error);
      // Error handling is managed by parent component
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderQuestion = (question) => {
    const questionId = question.id;
    const selectedAnswer = answers[questionId];
    const hasError = validationErrors[questionId];
    const fieldIds = formAccessibility.generateFieldIds(`question-${questionId}`);

    switch (question.type) {
      case 'multiple_choice':
        return (
          <fieldset className="space-y-3">
            <legend className="sr-only">
              {question.question} - Multiple choice question
            </legend>
            {question.options.map((option, index) => {
              const optionId = `${fieldIds.fieldId}-option-${index}`;
              return (
                <label
                  key={index}
                  htmlFor={optionId}
                  className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:bg-gray-50 focus-within:ring-3 focus-within:ring-blue-500 focus-within:ring-offset-2 touch-target-large ${
                    selectedAnswer === index
                      ? 'border-blue-600 bg-blue-50'
                      : hasError
                      ? 'border-red-400'
                      : 'border-gray-300'
                  }`}
                >
                  <input
                    ref={(el) => optionRefs.current[index] = el}
                    id={optionId}
                    type="radio"
                    name={`question-${questionId}`}
                    value={index}
                    checked={selectedAnswer === index}
                    onChange={() => handleAnswerChange(questionId, index)}
                    onKeyDown={(e) => handleOptionKeyDown(e, index, question.options.length, () => handleAnswerChange(questionId, index))}
                    className="mt-1 h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-400"
                    aria-describedby={hasError ? `error-${questionId}` : undefined}
                  />
                  <span className="ml-3 text-gray-900 flex-1 mobile:text-base tablet:text-lg">
                    {option}
                  </span>
                </label>
              );
            })}
          </fieldset>
        );

      case 'true_false':
        return (
          <fieldset className="space-y-3">
            <legend className="sr-only">
              {question.question} - True or false question
            </legend>
            {['True', 'False'].map((option, index) => {
              const optionId = `${fieldIds.fieldId}-option-${index}`;
              return (
                <label
                  key={index}
                  htmlFor={optionId}
                  className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:bg-gray-50 focus-within:ring-3 focus-within:ring-blue-500 focus-within:ring-offset-2 touch-target-large ${
                    selectedAnswer === index
                      ? 'border-blue-600 bg-blue-50'
                      : hasError
                      ? 'border-red-400'
                      : 'border-gray-300'
                  }`}
                >
                  <input
                    ref={(el) => optionRefs.current[index] = el}
                    id={optionId}
                    type="radio"
                    name={`question-${questionId}`}
                    value={index}
                    checked={selectedAnswer === index}
                    onChange={() => handleAnswerChange(questionId, index)}
                    onKeyDown={(e) => handleOptionKeyDown(e, index, 2, () => handleAnswerChange(questionId, index))}
                    className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-400"
                    aria-describedby={hasError ? `error-${questionId}` : undefined}
                  />
                  <span className="ml-3 text-gray-900 mobile:text-base tablet:text-lg">
                    {option}
                  </span>
                </label>
              );
            })}
          </fieldset>
        );

      case 'text':
        const textFieldAria = formAccessibility.getFieldAria(fieldIds, hasError, false);
        return (
          <div>
            <label htmlFor={fieldIds.fieldId} className="sr-only">
              {question.question} - Text answer
            </label>
            <textarea
              {...textFieldAria}
              value={selectedAnswer || ''}
              onChange={(e) => handleAnswerChange(questionId, e.target.value)}
              placeholder="Enter your answer here..."
              rows={4}
              className={`input-field resize-none mobile:text-base tablet:text-lg ${
                hasError ? 'input-field-error' : ''
              }`}
              aria-label={ariaLabels.fieldDescription('Text answer', true, 'Provide a detailed response')}
            />
          </div>
        );

      default:
        return (
          <div className="text-gray-500 italic">
            Unsupported question type: {question.type}
          </div>
        );
    }
  };

  return (
    <div className={`max-w-4xl mx-auto ${className}`}>
      {/* Survey Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 mobile:text-xl tablet:text-2xl">
            {surveyData.subject_name || surveyData.subject} Assessment
          </h2>
          <div className="text-sm text-gray-500 mobile:text-xs tablet:text-sm">
            Question {currentQuestionIndex + 1} of {totalQuestions}
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2 mobile:h-3">
          <div
            className="bg-primary-600 h-2 mobile:h-3 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progressPercentage}%` }}
            role="progressbar"
            aria-valuenow={Math.round(progressPercentage)}
            aria-valuemin="0"
            aria-valuemax="100"
            aria-label={`Survey progress: ${Math.round(progressPercentage)}% complete`}
          />
        </div>
      </div>

      {/* Question Card */}
      <div className="card mb-6">
        {/* Question Header */}
        <div className="mb-6">
          <div className="flex items-start justify-between mb-4">
            <h3 
              ref={questionRef}
              className="text-lg font-semibold text-gray-900 flex-1 mobile:text-base tablet:text-lg"
              tabIndex="-1"
              id={`question-${currentQuestion.id}-title`}
            >
              {currentQuestion.question}
            </h3>
            {currentQuestion.difficulty && (
              <span 
                className={`ml-4 px-2 py-1 text-xs font-medium rounded-full flex-shrink-0 ${
                  currentQuestion.difficulty === 'beginner'
                    ? 'bg-green-100 text-green-800'
                    : currentQuestion.difficulty === 'intermediate'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}
                aria-label={`Difficulty level: ${currentQuestion.difficulty}`}
              >
                {currentQuestion.difficulty}
              </span>
            )}
          </div>
          
          {currentQuestion.topic && (
            <div className="text-sm text-gray-600 mb-4">
              <span className="font-medium">Topic:</span> {currentQuestion.topic.replace('_', ' ')}
            </div>
          )}
        </div>

        {/* Question Content */}
        <div className="mb-6">
          {renderQuestion(currentQuestion)}
          
          {/* Validation Error */}
          {validationErrors[currentQuestion.id] && (
            <div 
              ref={errorRef}
              id={`error-${currentQuestion.id}`}
              className="mt-3 text-sm text-red-800 flex items-center bg-red-50 border border-red-200 rounded-lg p-3"
              role="alert"
              aria-live="assertive"
            >
              <svg className="h-5 w-5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {validationErrors[currentQuestion.id]}
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between items-center pt-6 border-t-2 border-gray-200">
          <button
            onClick={handlePrevious}
            disabled={isFirstQuestion}
            className={`flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-3 focus:ring-blue-500 focus:ring-offset-2 touch-target ${
              isFirstQuestion
                ? 'btn-disabled'
                : 'btn-secondary'
            }`}
            aria-label={`Go to previous question. Currently on question ${currentQuestionIndex + 1} of ${totalQuestions}`}
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Previous
          </button>

          <div className="flex space-x-3">
            {!isLastQuestion ? (
              <button
                onClick={handleNext}
                className="flex items-center btn-primary touch-target"
                aria-label={`Go to next question. Currently on question ${currentQuestionIndex + 1} of ${totalQuestions}`}
              >
                Next
                <svg className="h-4 w-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className={`flex items-center touch-target ${
                  isSubmitting
                    ? 'btn-disabled'
                    : 'btn-success'
                }`}
                aria-label={`Submit survey with ${Object.keys(answers).length} answers`}
              >
                {isSubmitting ? (
                  <>
                    <div className="loading-spinner h-4 w-4 border-white mr-2" aria-hidden="true"></div>
                    Submitting...
                    <span className="sr-only">Please wait while your survey is being submitted</span>
                  </>
                ) : (
                  <>
                    Submit Survey
                    <svg className="h-4 w-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Survey Info */}
      <div className="text-center text-sm text-gray-500">
        <p>
          This assessment helps us understand your current knowledge level to create a personalized learning path.
        </p>
        {surveyData.metadata?.topics_covered && (
          <p className="mt-2">
            Topics covered: {surveyData.metadata.topics_covered.join(', ').replace(/_/g, ' ')}
          </p>
        )}
      </div>
    </div>
  );
};

Survey.propTypes = {
  surveyData: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    subject: PropTypes.string.isRequired,
    subject_name: PropTypes.string,
    user_id: PropTypes.string.isRequired,
    questions: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
        question: PropTypes.string.isRequired,
        type: PropTypes.oneOf(['multiple_choice', 'true_false', 'text']).isRequired,
        options: PropTypes.array,
        difficulty: PropTypes.oneOf(['beginner', 'intermediate', 'advanced']),
        topic: PropTypes.string
      })
    ).isRequired,
    metadata: PropTypes.shape({
      topics_covered: PropTypes.arrayOf(PropTypes.string)
    })
  }),
  onSubmit: PropTypes.func.isRequired,
  onProgress: PropTypes.func,
  isLoading: PropTypes.bool,
  error: PropTypes.string,
  className: PropTypes.string
};

export default Survey;