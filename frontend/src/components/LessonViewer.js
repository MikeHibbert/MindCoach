import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import LessonService from '../services/lessonService';
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
  
  // Refs for accessibility
  const lessonContentRef = useRef(null);
  const sidebarRef = useRef(null);
  const navigationRef = useRef(null);
  const lessonRefs = useRef([]);

  // Load lesson list and progress on component mount
  useEffect(() => {
    if (userId && subject) {
      loadLessonList();
      loadProgress();
      loadCompletionStatus();
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