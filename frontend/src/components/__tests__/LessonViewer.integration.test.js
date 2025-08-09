import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import LessonViewer from '../LessonViewer';
import LessonService from '../../services/lessonService';

// Mock the LessonService but allow real API calls in integration tests
jest.mock('../../services/lessonService');

// Mock ReactMarkdown and related modules
jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }) {
    return <div data-testid="markdown-content">{children}</div>;
  };
});

jest.mock('remark-gfm', () => ({}));
jest.mock('rehype-highlight', () => ({}));

describe('LessonViewer Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('integrates with lesson API to load and display lessons', async () => {
    // Mock successful API responses
    const mockLessons = [
      {
        lesson_number: 1,
        title: 'Python Basics',
        estimated_time: '30 minutes',
        difficulty: 'beginner',
        topics: ['variables', 'data types']
      },
      {
        lesson_number: 2,
        title: 'Control Flow',
        estimated_time: '45 minutes',
        difficulty: 'intermediate',
        topics: ['if statements', 'loops']
      }
    ];

    const mockLesson = {
      lesson_number: 1,
      title: 'Python Basics',
      estimated_time: '30 minutes',
      difficulty: 'beginner',
      topics: ['variables', 'data types'],
      content: '# Python Basics\n\nLearn about variables and data types.\n\n```python\nx = 42\nprint(x)\n```'
    };

    const mockProgress = {
      user_id: 'user123',
      subject: 'python',
      total_lessons_generated: 2,
      available_lessons: 2,
      progress_percentage: 50.0,
      skill_level: 'beginner'
    };

    LessonService.listLessons.mockResolvedValue({
      success: true,
      lessons: mockLessons
    });

    LessonService.getLesson.mockResolvedValue({
      success: true,
      lesson: mockLesson
    });

    LessonService.getLessonProgress.mockResolvedValue({
      success: true,
      progress: mockProgress
    });

    render(<LessonViewer userId="user123" subject="python" />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    // Verify API calls were made
    expect(LessonService.listLessons).toHaveBeenCalledWith('user123', 'python');
    expect(LessonService.getLesson).toHaveBeenCalledWith('user123', 'python', 1);
    expect(LessonService.getLessonProgress).toHaveBeenCalledWith('user123', 'python');

    // Verify content is displayed
    expect(screen.getByText('Python Basics')).toBeInTheDocument();
    expect(screen.getByText('30 minutes')).toBeInTheDocument();
    expect(screen.getByText('beginner')).toBeInTheDocument();
    expect(screen.getByText('variables')).toBeInTheDocument();
    expect(screen.getByText('data types')).toBeInTheDocument();
  });

  test('handles lesson loading errors gracefully', async () => {
    LessonService.listLessons.mockResolvedValue({
      success: true,
      lessons: [
        {
          lesson_number: 1,
          title: 'Python Basics',
          estimated_time: '30 minutes',
          difficulty: 'beginner',
          topics: ['variables']
        }
      ]
    });

    LessonService.getLessonProgress.mockResolvedValue({
      success: true,
      progress: {
        user_id: 'user123',
        subject: 'python',
        total_lessons_generated: 1,
        available_lessons: 1,
        progress_percentage: 100.0
      }
    });

    // Mock lesson loading failure
    LessonService.getLesson.mockRejectedValue(new Error('Lesson not found'));

    render(<LessonViewer userId="user123" subject="python" />);

    // Wait for error to be displayed
    await waitFor(() => {
      expect(screen.getByText('Error loading lesson')).toBeInTheDocument();
    });

    expect(screen.getByText('Lesson not found')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();

    // Test retry functionality
    LessonService.getLesson.mockResolvedValue({
      success: true,
      lesson: {
        lesson_number: 1,
        title: 'Python Basics',
        content: '# Python Basics\n\nContent loaded successfully.'
      }
    });

    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
  });

  test('handles subscription required error', async () => {
    LessonService.listLessons.mockResolvedValue({
      success: true,
      lessons: []
    });

    LessonService.getLessonProgress.mockResolvedValue({
      success: true,
      progress: {
        user_id: 'user123',
        subject: 'python',
        total_lessons_generated: 0,
        available_lessons: 0,
        progress_percentage: 0
      }
    });

    const subscriptionError = new Error('Active subscription required for python');
    subscriptionError.type = 'subscription_required';
    subscriptionError.status = 403;

    LessonService.getLesson.mockRejectedValue(subscriptionError);

    render(<LessonViewer userId="user123" subject="python" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading lesson')).toBeInTheDocument();
    });

    expect(screen.getByText('Active subscription required for python')).toBeInTheDocument();
  });

  test('caches lessons to reduce API calls', async () => {
    const mockLessons = [
      {
        lesson_number: 1,
        title: 'Lesson 1',
        estimated_time: '30 minutes',
        difficulty: 'beginner',
        topics: ['topic1']
      },
      {
        lesson_number: 2,
        title: 'Lesson 2',
        estimated_time: '45 minutes',
        difficulty: 'intermediate',
        topics: ['topic2']
      }
    ];

    const mockLesson1 = {
      lesson_number: 1,
      title: 'Lesson 1',
      content: '# Lesson 1 Content'
    };

    const mockLesson2 = {
      lesson_number: 2,
      title: 'Lesson 2',
      content: '# Lesson 2 Content'
    };

    LessonService.listLessons.mockResolvedValue({
      success: true,
      lessons: mockLessons
    });

    LessonService.getLessonProgress.mockResolvedValue({
      success: true,
      progress: {
        user_id: 'user123',
        subject: 'python',
        total_lessons_generated: 2,
        available_lessons: 2,
        progress_percentage: 50.0
      }
    });

    LessonService.getLesson.mockImplementation((userId, subject, lessonNumber) => {
      if (lessonNumber === 1) {
        return Promise.resolve({ success: true, lesson: mockLesson1 });
      } else if (lessonNumber === 2) {
        return Promise.resolve({ success: true, lesson: mockLesson2 });
      }
    });

    render(<LessonViewer userId="user123" subject="python" />);

    // Wait for initial lesson to load
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    // Navigate to lesson 2
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Lesson 2' })).toBeInTheDocument();
    });

    // Navigate back to lesson 1
    const previousButton = screen.getByText('Previous');
    fireEvent.click(previousButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Lesson 1' })).toBeInTheDocument();
    });

    // Verify lesson 1 was only loaded once (cached on second access)
    expect(LessonService.getLesson).toHaveBeenCalledTimes(2); // Once for lesson 1, once for lesson 2
  });

  test('handles network errors gracefully', async () => {
    const networkError = new Error('Network error - please check your connection');
    networkError.type = 'network_error';

    LessonService.listLessons.mockRejectedValue(networkError);
    LessonService.getLessonProgress.mockRejectedValue(networkError);
    LessonService.getLesson.mockRejectedValue(networkError);

    render(<LessonViewer userId="user123" subject="python" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading lesson')).toBeInTheDocument();
    });

    expect(screen.getByText('Network error - please check your connection')).toBeInTheDocument();
  });

  test('updates progress as user navigates through lessons', async () => {
    const mockLessons = [
      {
        lesson_number: 1,
        title: 'Lesson 1',
        estimated_time: '30 minutes',
        difficulty: 'beginner',
        topics: ['topic1']
      },
      {
        lesson_number: 2,
        title: 'Lesson 2',
        estimated_time: '45 minutes',
        difficulty: 'intermediate',
        topics: ['topic2']
      },
      {
        lesson_number: 3,
        title: 'Lesson 3',
        estimated_time: '60 minutes',
        difficulty: 'advanced',
        topics: ['topic3']
      }
    ];

    LessonService.listLessons.mockResolvedValue({
      success: true,
      lessons: mockLessons
    });

    LessonService.getLessonProgress.mockResolvedValue({
      success: true,
      progress: {
        user_id: 'user123',
        subject: 'python',
        total_lessons_generated: 3,
        available_lessons: 3,
        progress_percentage: 33.3
      }
    });

    LessonService.getLesson.mockImplementation((userId, subject, lessonNumber) => {
      return Promise.resolve({
        success: true,
        lesson: {
          lesson_number: lessonNumber,
          title: `Lesson ${lessonNumber}`,
          content: `# Lesson ${lessonNumber} Content`
        }
      });
    });

    render(<LessonViewer userId="user123" subject="python" />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Lesson 1 of 3')).toBeInTheDocument();
    });

    // Navigate to lesson 2
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText('Lesson 2 of 3')).toBeInTheDocument();
    });

    // Navigate to lesson 3
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText('Lesson 3 of 3')).toBeInTheDocument();
    });

    // Verify next button is disabled on last lesson
    expect(nextButton.closest('button')).toBeDisabled();
  });

  test('handles empty lesson list gracefully', async () => {
    LessonService.listLessons.mockResolvedValue({
      success: true,
      lessons: []
    });

    LessonService.getLessonProgress.mockResolvedValue({
      success: true,
      progress: {
        user_id: 'user123',
        subject: 'python',
        total_lessons_generated: 0,
        available_lessons: 0,
        progress_percentage: 0
      }
    });

    LessonService.getLesson.mockRejectedValue(new Error('No lessons available'));

    render(<LessonViewer userId="user123" subject="python" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading lesson')).toBeInTheDocument();
    });

    expect(screen.getByText('No lessons available')).toBeInTheDocument();
  });
});