import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import LessonService from '../services/lessonService';
import PipelineService from '../services/pipelineService';
import PipelineProgressTracker from './PipelineProgressTracker';
import { 
  announceToScreenReader, 
  keyboardNavigation, 
  ariaLabels, 
  focusManagement 
} from '../utils/accessibility';

const LessonViewer = ({ userId, subject, initialLessonNumber = 1 }) => {
  const [lessons, setLessons] = useState([]);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [currentLessonNumber, setCurrentLessonNumber] = useState(initialLessonNumber);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lessonCache, setLessonCache] = useState(new Map());
  const [completedLessons, setCompletedLessons] = useState(new Set());
  
  // New LangChain data states
  const [curriculumScheme, setCurriculumScheme] = useState(null);
  const [lessonPlans, setLessonPlans] = useState(null);
  const [showCurriculumOverview, setShowCurriculumOverview] = useState(false);
  const [showLessonPlanPreview, setShowLessonPlanPreview] = useState(false);
  const [isLangChainGenerated, setIsLangChainGenerated] = useState(false);
  const [needsGeneration, setNeedsGeneration] = useState(false);
  
  // Refs for accessibility
  const lessonContentRef = useRef(null);
  const sidebarRef = useRef(null);
  const navigationRef = useRef(null);
  const lessonRefs = useRef([]);
  const curriculumRef = useRef(null);

  // Load lesson list and progress on component mount
  useEffect(() => {
    if (userId && subject) {
      loadLessonList();
      loadProgress();
      loadCompletionStatus();
      loadLangChainData();
    }
  }, [userId, subject]);

  // Load specific lesson when lesson number changes
  useEffect(() => {
    if (userId && subject && currentLessonNumber) {
      loadLesson(currentLessonNumber);
    }
  }, [userId, subject, currentLessonNumber]);

  const loadLessonList = async () => {
    try {
      const response = await LessonService.listLessons(userId, subject);
      if (response.success) {
        setLessons(response.lessons || []);
      } else {
        setError(response.message || 'Failed to load lesson list');
      }
    } catch (err) {
      setError(err.message || 'Failed to load lesson list');
    }
  };

  const loadProgress = async () => {
    try {
      const response = await LessonService.getLessonProgress(userId, subject);
      if (response.success) {
        setProgress(response.progress);
      }
    } catch (err) {
      console.warn('Failed to load progress:', err.message);
    }
  };

  const loadCompletionStatus = async () => {
    try {
      const response = await LessonService.getLessonCompletionStatus(userId, subject);
      if (response.success && response.completed_lessons) {
        setCompletedLessons(new Set(response.completed_lessons));
      }
    } catch (err) {
      console.warn('Failed to load completion status:', err.message);
    }
  };

  const loadLangChainData = async () => {
    try {
      // Try to load curriculum scheme
      const curriculumResponse = await PipelineService.getCurriculumScheme(userId, subject);
      if (curriculumResponse.success) {
        setCurriculumScheme(curriculumResponse.curriculum);
        setIsLangChainGenerated(true);
      }
    } catch (err) {
      console.debug('No curriculum scheme found - may need generation:', err.message);
    }

    try {
      // Try to load lesson plans
      const lessonPlansResponse = await PipelineService.getLessonPlans(userId, subject);
      if (lessonPlansResponse.success) {
        setLessonPlans(lessonPlansResponse.lesson_plans);
      }
    } catch (err) {
      console.debug('No lesson plans found:', err.message);
    }

    // Check if lessons exist, if not, show generation option
    try {
      const lessonListResponse = await LessonService.listLessons(userId, subject);
      if (!lessonListResponse.success || !lessonListResponse.lessons || lessonListResponse.lessons.length === 0) {
        setNeedsGeneration(true);
      }
    } catch (err) {
      setNeedsGeneration(true);
    }
  };

  const loadLesson = useCallback(async (lessonNumber) => {
    // Check cache first
    if (lessonCache.has(lessonNumber)) {
      setCurrentLesson(lessonCache.get(lessonNumber));
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await LessonService.getLesson(userId, subject, lessonNumber);
      if (response.success) {
        const lessonData = response.lesson;
        setCurrentLesson(lessonData);
        
        // Cache the lesson
        setLessonCache(prev => new Map(prev).set(lessonNumber, lessonData));
      } else {
        setError(response.message || 'Failed to load lesson');
      }
    } catch (err) {
      setError(err.message || 'Failed to load lesson');
    } finally {
      setLoading(false);
    }
  }, [userId, subject, lessonCache]);

  const navigateToLesson = (lessonNumber) => {
    if (lessonNumber >= 1 && lessonNumber <= lessons.length) {
      // Mark current lesson as completed when navigating away
      if (currentLessonNumber && currentLessonNumber !== lessonNumber) {
        markLessonAsCompleted(currentLessonNumber);
      }
      setCurrentLessonNumber(lessonNumber);
      
      // Announce navigation to screen readers
      const lesson = lessons[lessonNumber - 1];
      announceToScreenReader(`Navigated to lesson ${lessonNumber}: ${lesson?.title || 'Loading...'}`);
      
      // Focus management
      if (lessonContentRef.current) {
        focusManagement.setFocus(lessonContentRef.current, 300);
      }
    }
  };

  // Handle keyboard navigation for lesson sidebar
  const handleLessonKeyDown = (e, lessonIndex) => {
    keyboardNavigation.handleArrowKeys(
      e,
      lessons,
      lessonIndex,
      (newIndex) => {
        lessonRefs.current[newIndex]?.focus();
      }
    );

    keyboardNavigation.handleActivation(e, () => {
      navigateToLesson(lessonIndex + 1);
    });
  };

  const markLessonAsCompleted = async (lessonNumber) => {
    if (completedLessons.has(lessonNumber)) {
      return; // Already completed
    }

    try {
      await LessonService.markLessonCompleted(userId, subject, lessonNumber);
      
      // Update local state
      setCompletedLessons(prev => new Set([...prev, lessonNumber]));
      
      // Announce completion
      const lesson = lessons[lessonNumber - 1];
      announceToScreenReader(`Lesson ${lessonNumber} "${lesson?.title}" marked as completed`);
      
      // Update progress
      setProgress(prevProgress => {
        if (!prevProgress) return prevProgress;
        
        const updatedProgress = { ...prevProgress };
        const totalCompleted = completedLessons.size + 1;
        updatedProgress.progress_percentage = (totalCompleted / lessons.length) * 100;
        
        return updatedProgress;
      });
    } catch (err) {
      console.warn(`Failed to mark lesson ${lessonNumber} as completed:`, err.message);
      announceToScreenReader(`Error marking lesson as completed: ${err.message}`, 'assertive');
    }
  };

  const handlePipelineComplete = (status) => {
    // Reload lesson data after pipeline completion
    loadLessonList();
    loadLangChainData();
    setNeedsGeneration(false);
    
    announceToScreenReader('Learning content generated successfully! Your personalized lessons are now available.', 'assertive');
  };

  const handlePipelineError = (error) => {
    console.error('Pipeline generation error:', error);
    announceToScreenReader(`Content generation failed: ${error.message}`, 'assertive');
  };

  const toggleCurriculumOverview = () => {
    setShowCurriculumOverview(prev => !prev);
    
    if (!showCurriculumOverview && curriculumRef.current) {
      focusManagement.setFocus(curriculumRef.current, 300);
    }
  };

  const toggleLessonPlanPreview = () => {
    setShowLessonPlanPreview(prev => !prev);
  };

  const getCurrentLessonPlan = () => {
    if (!lessonPlans || !lessonPlans.lesson_plans) return null;
    
    return lessonPlans.lesson_plans.find(plan => 
      plan.lesson_id === currentLessonNumber
    );
  };

  const goToPreviousLesson = () => {
    if (currentLessonNumber > 1) {
      navigateToLesson(currentLessonNumber - 1);
    }
  };

  const goToNextLesson = () => {
    if (currentLessonNumber < lessons.length) {
      navigateToLesson(currentLessonNumber + 1);
    }
  };

  const renderQuizContent = (content) => {
    // Simple quiz detection and rendering
    // This is a basic implementation - can be enhanced based on quiz format
    const quizPattern = /```quiz\n([\s\S]*?)\n```/g;
    
    return content.replace(quizPattern, (match, quizContent) => {
      return `
<div class="quiz-container bg-blue-50 border-l-4 border-blue-400 p-4 my-6 rounded-r-lg">
  <h4 class="text-lg font-semibold text-blue-800 mb-3">📝 Practice Quiz</h4>
  <div class="quiz-content">
    ${quizContent}
  </div>
</div>`;
    });
  };

  const renderCurriculumOverview = () => {
    if (!curriculumScheme) return null;

    const curriculum = curriculumScheme.curriculum || curriculumScheme;

    return (
      <div 
        ref={curriculumRef}
        className="curriculum-overview bg-white border-2 border-blue-200 rounded-lg p-6 mb-6"
        role="region"
        aria-label="Curriculum overview"
        tabIndex="-1"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">
            📚 Course Curriculum Overview
          </h2>
          <button
            onClick={toggleCurriculumOverview}
            className="text-blue-600 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded p-1"
            aria-label="Close curriculum overview"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">Course Details</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-700">Subject:</span>
                <span className="font-medium text-gray-900 capitalize">{curriculum.subject}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">Skill Level:</span>
                <span className="font-medium text-gray-900 capitalize">{curriculum.skill_level}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">Total Lessons:</span>
                <span className="font-medium text-gray-900">{curriculum.total_lessons}</span>
              </div>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-900 mb-2">Learning Objectives</h3>
            <ul className="space-y-1 text-sm text-green-800" role="list">
              {curriculum.learning_objectives?.map((objective, index) => (
                <li key={index} className="flex items-start" role="listitem">
                  <span className="text-green-600 mr-2 mt-0.5">•</span>
                  {objective}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {curriculum.topics && curriculum.topics.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Lesson Topics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {curriculum.topics.map((topic, index) => {
                const lessonNumber = topic.lesson_id || index + 1;
                const isCompleted = completedLessons.has(lessonNumber);
                const isCurrent = lessonNumber === currentLessonNumber;

                return (
                  <button
                    key={lessonNumber}
                    onClick={() => navigateToLesson(lessonNumber)}
                    className={`text-left p-3 rounded-lg border-2 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      isCurrent
                        ? 'bg-blue-100 border-blue-400 text-blue-900'
                        : isCompleted
                        ? 'bg-green-50 border-green-300 text-green-800 hover:bg-green-100'
                        : 'bg-gray-50 border-gray-300 text-gray-800 hover:bg-gray-100'
                    }`}
                    aria-label={`Go to lesson ${lessonNumber}: ${topic.title}. ${isCompleted ? 'Completed' : 'Not completed'}`}
                  >
                    <div className="flex items-center">
                      <div 
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 ${
                          isCurrent
                            ? 'bg-blue-600 text-white'
                            : isCompleted
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-400 text-white'
                        }`}
                        aria-hidden="true"
                      >
                        {isCompleted ? '✓' : lessonNumber}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-sm">{topic.title}</div>
                        {topic.difficulty && (
                          <div className="text-xs opacity-75 capitalize">
                            {topic.difficulty}
                          </div>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderLessonPlanPreview = () => {
    const currentPlan = getCurrentLessonPlan();
    if (!currentPlan) return null;

    return (
      <div className="lesson-plan-preview bg-purple-50 border-2 border-purple-200 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-purple-900">
            📋 Lesson Plan Preview
          </h3>
          <button
            onClick={toggleLessonPlanPreview}
            className="text-purple-600 hover:text-purple-800 focus:outline-none focus:ring-2 focus:ring-purple-500 rounded p-1"
            aria-label="Close lesson plan preview"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-3">
          {currentPlan.learning_objectives && (
            <div>
              <h4 className="font-medium text-purple-900 mb-2">Learning Objectives</h4>
              <ul className="space-y-1 text-sm text-purple-800" role="list">
                {currentPlan.learning_objectives.map((objective, index) => (
                  <li key={index} className="flex items-start" role="listitem">
                    <span className="text-purple-600 mr-2 mt-0.5">•</span>
                    {objective}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {currentPlan.structure && (
            <div>
              <h4 className="font-medium text-purple-900 mb-2">Lesson Structure</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                {Object.entries(currentPlan.structure).map(([section, duration]) => (
                  <div key={section} className="bg-purple-100 rounded px-2 py-1">
                    <div className="font-medium text-purple-900 capitalize">
                      {section.replace('_', ' ')}
                    </div>
                    <div className="text-purple-700">{duration}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentPlan.activities && (
            <div>
              <h4 className="font-medium text-purple-900 mb-2">Activities</h4>
              <div className="flex flex-wrap gap-2">
                {currentPlan.activities.map((activity, index) => (
                  <span
                    key={index}
                    className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full"
                  >
                    {activity}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderLessonNavigation = () => (
    <nav 
      ref={navigationRef}
      className="lesson-navigation bg-white border-t-2 border-gray-200 p-4 sticky bottom-0"
      role="navigation"
      aria-label="Lesson navigation"
    >
      <div className="flex justify-between items-center max-w-4xl mx-auto">
        {/* Previous Button */}
        <button
          onClick={goToPreviousLesson}
          disabled={currentLessonNumber <= 1}
          className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-3 focus:ring-blue-500 focus:ring-offset-2 touch-target ${
            currentLessonNumber <= 1
              ? 'btn-disabled'
              : 'btn-primary'
          }`}
          aria-label={`Go to previous lesson. Currently on lesson ${currentLessonNumber} of ${lessons.length}`}
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Previous
        </button>

        {/* Lesson Progress */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-700 font-medium">
            Lesson {currentLessonNumber} of {lessons.length}
          </span>
          {progress && (
            <div 
              className="w-32 bg-gray-200 rounded-full h-3 border border-gray-300"
              role="progressbar"
              aria-valuenow={currentLessonNumber}
              aria-valuemin="1"
              aria-valuemax={lessons.length}
              aria-label={ariaLabels.navigation(currentLessonNumber, lessons.length, 'lesson')}
            >
              <div
                className="bg-blue-600 h-full rounded-full transition-all duration-300"
                style={{ width: `${(currentLessonNumber / lessons.length) * 100}%` }}
              />
            </div>
          )}
        </div>

        {/* Next Button */}
        <button
          onClick={goToNextLesson}
          disabled={currentLessonNumber >= lessons.length}
          className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-3 focus:ring-blue-500 focus:ring-offset-2 touch-target ${
            currentLessonNumber >= lessons.length
              ? 'btn-disabled'
              : 'btn-primary'
          }`}
          aria-label={`Go to next lesson. Currently on lesson ${currentLessonNumber} of ${lessons.length}`}
        >
          Next
          <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </nav>
  );

  const renderLessonSidebar = () => (
    <nav 
      ref={sidebarRef}
      className="lesson-sidebar w-full lg:w-80 bg-white border-r-2 border-gray-200 p-4 lg:sticky lg:top-0 lg:h-screen lg:overflow-y-auto"
      role="navigation"
      aria-label="Course lessons"
    >
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Course Progress</h3>
      
      {/* LangChain Features */}
      {isLangChainGenerated && (
        <div className="mb-4 space-y-2">
          {curriculumScheme && (
            <button
              onClick={toggleCurriculumOverview}
              className="w-full text-left p-2 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="View curriculum overview"
            >
              <div className="flex items-center">
                <svg className="w-4 h-4 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-sm font-medium text-blue-900">Curriculum Overview</span>
              </div>
            </button>
          )}
          
          {lessonPlans && (
            <button
              onClick={toggleLessonPlanPreview}
              className="w-full text-left p-2 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500"
              aria-label="View lesson plan preview"
            >
              <div className="flex items-center">
                <svg className="w-4 h-4 text-purple-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <span className="text-sm font-medium text-purple-900">Lesson Plan Preview</span>
              </div>
            </button>
          )}
        </div>
      )}
      
      {progress && (
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-700 mb-2">
            <span>Overall Progress</span>
            <span>{Math.round(progress.progress_percentage)}%</span>
          </div>
          <div 
            className="w-full bg-gray-200 rounded-full h-3 border border-gray-300"
            role="progressbar"
            aria-valuenow={Math.round(progress.progress_percentage)}
            aria-valuemin="0"
            aria-valuemax="100"
            aria-label={ariaLabels.progressBar(
              completedLessons.size, 
              lessons.length, 
              'Course completion'
            )}
          >
            <div
              className="bg-green-600 h-full rounded-full transition-all duration-300"
              style={{ width: `${progress.progress_percentage}%` }}
            />
          </div>
        </div>
      )}

      <div className="space-y-2" role="list" aria-label="Lesson list">
        {lessons.map((lesson, index) => {
          const lessonNumber = index + 1;
          const isActive = lessonNumber === currentLessonNumber;
          const isCompleted = completedLessons.has(lessonNumber);
          
          return (
            <button
              key={lessonNumber}
              ref={(el) => lessonRefs.current[index] = el}
              onClick={() => navigateToLesson(lessonNumber)}
              onKeyDown={(e) => handleLessonKeyDown(e, index)}
              className={`w-full text-left p-3 rounded-lg transition-colors focus:outline-none focus:ring-3 focus:ring-blue-500 focus:ring-offset-2 touch-target ${
                isActive
                  ? 'bg-blue-100 border-2 border-blue-600 text-blue-900'
                  : isCompleted
                  ? 'bg-green-50 border-2 border-green-300 text-green-800 hover:bg-green-100'
                  : 'bg-gray-50 border-2 border-gray-300 text-gray-800 hover:bg-gray-100'
              }`}
              aria-current={isActive ? 'page' : undefined}
              aria-label={`Lesson ${lessonNumber}: ${lesson.title}. ${
                isCompleted ? 'Completed' : 'Not completed'
              }. ${lesson.estimated_time}. Difficulty: ${lesson.difficulty}`}
              role="listitem"
            >
              <div className="flex items-center">
                <div 
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold mr-3 ${
                    isActive
                      ? 'bg-blue-700 text-white'
                      : isCompleted
                      ? 'bg-green-700 text-white'
                      : 'bg-gray-400 text-gray-100'
                  }`}
                  aria-hidden="true"
                >
                  {isCompleted ? '✓' : lessonNumber}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-sm">{lesson.title}</div>
                  <div className="text-xs opacity-75">
                    {lesson.estimated_time} • {lesson.difficulty}
                  </div>
                </div>
                {isActive && (
                  <span className="sr-only">(current lesson)</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </nav>
  );

  if (!userId || !subject) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center text-gray-600">
          Please select a subject to view lessons.
        </div>
      </div>
    );
  }

  if (needsGeneration) {
    return (
      <div className="lesson-viewer-container min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto p-6">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Generate Your Personalized Learning Content
            </h1>
            <p className="text-lg text-gray-600 mb-6">
              Create AI-powered lessons tailored to your skill level and learning goals for {subject}.
            </p>
          </div>
          
          <PipelineProgressTracker
            userId={userId}
            subject={subject}
            onComplete={handlePipelineComplete}
            onError={handlePipelineError}
            className="max-w-2xl mx-auto"
          />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-red-800 font-medium">Error loading lesson</span>
          </div>
          <p className="text-red-700 mt-2">{error}</p>
          <button
            onClick={() => loadLesson(currentLessonNumber)}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="lesson-viewer-container min-h-screen bg-gray-50">
      <div className="flex flex-col lg:flex-row">
        {/* Sidebar - Hidden on mobile, shown on tablet and desktop */}
        <div className="hidden md:block">
          {renderLessonSidebar()}
        </div>

        {/* Main Content */}
        <div className="flex-1 min-h-screen pb-20">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Loading lesson...</span>
            </div>
          ) : currentLesson ? (
            <div className="max-w-4xl mx-auto p-6">
              {/* Curriculum Overview */}
              {showCurriculumOverview && renderCurriculumOverview()}
              
              {/* Lesson Plan Preview */}
              {showLessonPlanPreview && renderLessonPlanPreview()}
              
              {/* Lesson Header */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
                  <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                      {currentLesson.title}
                    </h1>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {currentLesson.estimated_time}
                      </span>
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        {currentLesson.difficulty}
                      </span>
                      {isLangChainGenerated && (
                        <span className="flex items-center bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">
                          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                          AI Generated
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Mobile lesson selector */}
                  <div className="md:hidden mt-4">
                    <select
                      value={currentLessonNumber}
                      onChange={(e) => navigateToLesson(parseInt(e.target.value))}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      {lessons.map((lesson, index) => (
                        <option key={index + 1} value={index + 1}>
                          Lesson {index + 1}: {lesson.title}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Learning Objectives from Lesson Plan */}
                {getCurrentLessonPlan()?.learning_objectives && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">Learning Objectives</h3>
                    <ul className="space-y-1 text-sm text-gray-700" role="list">
                      {getCurrentLessonPlan().learning_objectives.map((objective, index) => (
                        <li key={index} className="flex items-start" role="listitem">
                          <span className="text-blue-600 mr-2 mt-0.5">•</span>
                          {objective}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Topics */}
                {currentLesson.topics && currentLesson.topics.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {currentLesson.topics.map((topic, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Lesson Content */}
              <div 
              ref={lessonContentRef}
              className="bg-white rounded-lg shadow-sm border-2 border-gray-200 p-6"
              tabIndex="-1"
              role="main"
              aria-label="Lesson content"
            >
                <div className="prose prose-lg max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeHighlight]}
                    components={{
                      // Custom rendering for code blocks with accessibility
                      code: ({ node, inline, className, children, ...props }) => {
                        const languageMatch = /language-(\w+)/.exec(className || '');
                        return !inline && languageMatch ? (
                          <div className="relative" role="region" aria-label={`Code example in ${languageMatch[1]}`}>
                            <div className="absolute top-2 right-2 text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded border">
                              {languageMatch[1]}
                            </div>
                            <pre className={className} {...props} tabIndex="0">
                              <code>{children}</code>
                            </pre>
                          </div>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      },
                      // Custom rendering for blockquotes with accessibility
                      blockquote: ({ children }) => (
                        <blockquote 
                          className="border-l-4 border-blue-500 bg-blue-50 p-4 my-4 rounded-r-lg"
                          role="note"
                          aria-label="Important note"
                        >
                          {children}
                        </blockquote>
                      ),
                      // Accessible headings
                      h1: ({ children }) => (
                        <h1 className="text-2xl font-bold text-gray-900 mb-4" tabIndex="0">
                          {children}
                        </h1>
                      ),
                      h2: ({ children }) => (
                        <h2 className="text-xl font-semibold text-gray-900 mb-3" tabIndex="0">
                          {children}
                        </h2>
                      ),
                      h3: ({ children }) => (
                        <h3 className="text-lg font-medium text-gray-900 mb-2" tabIndex="0">
                          {children}
                        </h3>
                      ),
                      // Accessible lists
                      ul: ({ children }) => (
                        <ul className="list-disc list-inside space-y-1 text-gray-800" role="list">
                          {children}
                        </ul>
                      ),
                      ol: ({ children }) => (
                        <ol className="list-decimal list-inside space-y-1 text-gray-800" role="list">
                          {children}
                        </ol>
                      ),
                      li: ({ children }) => (
                        <li className="text-gray-800" role="listitem">
                          {children}
                        </li>
                      ),
                    }}
                  >
                    {renderQuizContent(currentLesson.content)}
                  </ReactMarkdown>
                </div>

                {/* Lesson Completion */}
                <div className="mt-6 pt-6 border-t-2 border-gray-200">
                  {completedLessons.has(currentLessonNumber) ? (
                    <div 
                      className="flex items-center text-green-700 bg-green-50 border-2 border-green-200 rounded-lg p-3"
                      role="status"
                      aria-live="polite"
                    >
                      <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="font-medium">Lesson completed!</span>
                    </div>
                  ) : (
                    <button
                      onClick={() => markLessonAsCompleted(currentLessonNumber)}
                      className="btn-success focus:ring-green-500 touch-target"
                      aria-label={`Mark lesson ${currentLessonNumber} as completed`}
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Mark as Complete
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64">
              <div className="text-center text-gray-600">
                <p>No lesson content available.</p>
                <button
                  onClick={() => loadLesson(currentLessonNumber)}
                  className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Reload
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Navigation Footer */}
      {currentLesson && renderLessonNavigation()}
    </div>
  );
};

export default LessonViewer;