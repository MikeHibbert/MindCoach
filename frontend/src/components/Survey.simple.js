import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const Survey = () => {
  const { subject } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    // Simulate loading survey questions
    setTimeout(() => {
      setQuestions([
        {
          id: 1,
          question: `What is your current experience level with ${subject}?`,
          type: 'multiple_choice',
          options: [
            'Complete beginner - never used it',
            'Some basic knowledge - can write simple programs',
            'Intermediate - comfortable with most concepts',
            'Advanced - can build complex applications'
          ]
        },
        {
          id: 2,
          question: `What type of projects do you want to build with ${subject}?`,
          type: 'multiple_choice',
          options: [
            'Web applications',
            'Data analysis and science',
            'Mobile applications',
            'Desktop applications',
            'Games and interactive media'
          ]
        },
        {
          id: 3,
          question: `How much time can you dedicate to learning per week?`,
          type: 'multiple_choice',
          options: [
            '1-2 hours per week',
            '3-5 hours per week',
            '6-10 hours per week',
            'More than 10 hours per week'
          ]
        }
      ]);
      setLoading(false);
    }, 1000);
  }, [subject]);

  const handleAnswerSelect = (questionId, answerIndex) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answerIndex
    }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      // Simulate API call to submit survey
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';
      const response = await fetch(`${API_BASE_URL}/users/demo-user/subjects/${subject}/survey/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          answers: Object.entries(answers).map(([questionId, answerIndex]) => ({
            question_id: parseInt(questionId),
            answer_index: answerIndex,
            question: questions.find(q => q.id === parseInt(questionId))?.question,
            selected_option: questions.find(q => q.id === parseInt(questionId))?.options[answerIndex]
          }))
        }),
      });

      if (response.ok) {
        // Navigate to lessons page
        navigate(`/subjects/${subject}/lessons`);
      } else {
        throw new Error('Failed to submit survey');
      }
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  if (loading && questions.length === 0) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your {subject} assessment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-medium">Error</h3>
          <p className="text-red-700 mt-1">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Back to Subjects
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
  const isLastQuestion = currentQuestionIndex === questions.length - 1;
  const hasAnswered = answers[currentQuestion.id] !== undefined;

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900 capitalize">
            {subject} Assessment
          </h1>
          <span className="text-sm text-gray-500">
            {currentQuestionIndex + 1} of {questions.length}
          </span>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Question */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">
          {currentQuestion.question}
        </h2>

        <div className="space-y-3">
          {currentQuestion.options.map((option, index) => (
            <button
              key={index}
              onClick={() => handleAnswerSelect(currentQuestion.id, index)}
              className={`w-full text-left p-4 rounded-lg border-2 transition-all duration-200 ${
                answers[currentQuestion.id] === index
                  ? 'border-blue-600 bg-blue-50 text-blue-900'
                  : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center">
                <div className={`w-4 h-4 rounded-full border-2 mr-3 ${
                  answers[currentQuestion.id] === index
                    ? 'border-blue-600 bg-blue-600'
                    : 'border-gray-400'
                }`}>
                  {answers[currentQuestion.id] === index && (
                    <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                  )}
                </div>
                <span>{option}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center">
        <button
          onClick={handlePrevious}
          disabled={currentQuestionIndex === 0}
          className={`px-4 py-2 rounded-lg transition-colors ${
            currentQuestionIndex === 0
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Previous
        </button>

        <div className="flex space-x-3">
          {!isLastQuestion ? (
            <button
              onClick={handleNext}
              disabled={!hasAnswered}
              className={`px-6 py-2 rounded-lg transition-colors ${
                !hasAnswered
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!hasAnswered || loading}
              className={`px-6 py-2 rounded-lg transition-colors ${
                !hasAnswered || loading
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Submitting...
                </div>
              ) : (
                'Complete Assessment'
              )}
            </button>
          )}
        </div>
      </div>

      {/* Help Text */}
      <div className="mt-8 text-center text-sm text-gray-500">
        <p>This assessment helps us create a personalized learning path for you.</p>
        <p className="mt-1">Answer honestly to get the best recommendations.</p>
      </div>
    </div>
  );
};

export default Survey;