import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import LessonViewer from '../LessonViewer';
import LessonService from '../../services/lessonService';

// Mock the LessonService
jest.mock('../../services/lessonService');

// Mock ReactMarkdown and related modules
jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }) {
    return <div data-testid="markdown-content">{children}</div>;
  };
});

jest.mock('remark-gfm', () => ({}));
jest.mock('rehype-highlight', () => ({}));

describe('LessonViewer End-to-End Tests', () => {
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
    },
    {
      lesson_number: 3,
      title: 'Functions',
      estimated_time: '60 minutes',
      difficulty: 'intermediate',
      topics: ['functions', 'parameters']
    }
  ];

  const mockProgress = {
    user_id: 'user123',
    subject: 'python',
    total_lessons_generated: 3,
    available_lessons: 3,
    progress_percentage: 33.3,
    skill_level: 'beginner'
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    LessonService.listLessons.mockResolvedValue({
      success: true,
      lessons: mockLessons
    });

    LessonService.getLessonProgress.mockResolvedValue({
      success: true,
      progress: mockProgress
    });

    LessonService.getLessonCompletionStatus.mockResolvedValue({
      success: true,
      completed_lessons: []
    });

    LessonService.getLesson.mockImplementation((userId, subject, lessonNumber) => {
      return Promise.resolve({
        success: true,
        lesson: {
          lesson_number: lessonNumber,
          title: mockLessons[lessonNumber - 1].title,
          estimated_time: mockLessons[lessonNumber - 1].estimated_time,
          difficulty: mockLessons[lessonNumber - 1].difficulty,
          topics: mockLessons[lessonNumber - 1].topics,
          content: `# ${mockLessons[lessonNumber - 1].title}\n\nThis is lesson ${lessonNumber} content.\n\n\`\`\`python\nprint("Lesson ${lessonNumber}")\n\`\`\``
        }
      });
    });

    LessonService.markLessonCompleted.mockResolvedValue({
      success: true,
      message: 'Lesson marked as completed'
    });
  });

  test('complete lesson learning workflow', async () => {
    render(<LessonViewer userId="user123" subject="python" />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    // Verify initial state
    expect(screen.getByText('Python Basics')).toBeInTheDocument();
    expect(screen.getByText('Lesson 1 of 3')).toBeInTheDocument();
    expect(screen.getByText('Mark as Complete')).toBeInTheDocument();

    // Mark first lesson as complete
    const completeButton = screen.getByText('Mark as Complete');
    fireEvent.click(completeButton);

    await waitFor(() => {
      expect(screen.getByText('Lesson completed!')).toBeInTheDocument();
    });

    expect(LessonService.markLessonCompleted).toHaveBeenCalledWith('user123', 'python', 1);

    // Navigate to next lesson
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Control Flow' })).toBeInTheDocument();
    });

    expect(screen.getByText('Lesson 2 of 3')).toBeInTheDocument();
    expect(screen.getByText('Mark as Complete')).toBeInTheDocument();

    // Navigate to third lesson
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Functions' })).toBeInTheDocument();
    });

    expect(screen.getByText('Lesson 3 of 3')).toBeInTheDocument();

    // Verify next button is disabled on last lesson
    expect(nextButton.closest('button')).toBeDisabled();

    // Navigate back to first lesson
    const previousButton = screen.getByText('Previous');
    fireEvent.click(previousButton);
    fireEvent.click(previousButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Python Basics' })).toBeInTheDocument();
    });

    // Verify lesson is still marked as completed
    expect(screen.getByText('Lesson completed!')).toBeInTheDocument();
  });

  test('responsive navigation workflow', async () => {
    render(<LessonViewer userId="user123" subject="python" />);

    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    // Test sidebar navigation (desktop)
    const sidebarButtons = screen.getAllByText('Python Basics');
    expect(sidebarButtons.length).toBeGreaterThan(1); // One in main content, one in sidebar

    // Click on lesson 2 in sidebar
    const lesson2Button = screen.getByText('Control Flow');
    fireEvent.click(lesson2Button);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Control Flow' })).toBeInTheDocument();
    });

    expect(screen.getByText('Lesson 2 of 3')).toBeInTheDocument();

    // Test mobile selector (when available)
    const mobileSelector = screen.getByDisplayValue('Lesson 2: Control Flow');
    expect(mobileSelector).toBeInTheDocument();

    // Change selection via mobile dropdown
    fireEvent.change(mobileSelector, { target: { value: '3' } });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Functions' })).toBeInTheDocument();
    });
  });

  test('lesson completion tracking across navigation', async () => {
    // Mock some lessons as already completed
    LessonService.getLessonCompletionStatus.mockResolvedValue({
      success: true,
      completed_lessons: [1, 2]
    });

    render(<LessonViewer userId="user123" subject="python" />);

    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    // Verify first lesson shows as completed
    expect(screen.getByText('Lesson completed!')).toBeInTheDocument();

    // Navigate to second lesson
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Control Flow' })).toBeInTheDocument();
    });

    // Verify second lesson also shows as completed
    expect(screen.getByText('Lesson completed!')).toBeInTheDocument();

    // Navigate to third lesson
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Functions' })).toBeInTheDocument();
    });

    // Verify third lesson is not completed
    expect(screen.getByText('Mark as Complete')).toBeInTheDocument();

    // Complete the third lesson
    const completeButton = screen.getByText('Mark as Complete');
    fireEvent.click(completeButton);

    await waitFor(() => {
      expect(screen.getByText('Lesson completed!')).toBeInTheDocument();
    });

    expect(LessonService.markLessonCompleted).toHaveBeenCalledWith('user123', 'python', 3);
  });

  test('error recovery workflow', async () => {
    // Mock initial failure
    LessonService.getLesson.mockRejectedValueOnce(new Error('Network error'));

    render(<LessonViewer userId="user123" subject="python" />);

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText('Error loading lesson')).toBeInTheDocument();
    });

    expect(screen.getByText('Network error')).toBeInTheDocument();

    // Mock successful retry
    LessonService.getLesson.mockResolvedValue({
      success: true,
      lesson: {
        lesson_number: 1,
        title: 'Python Basics',
        content: '# Python Basics\n\nContent loaded successfully after retry.'
      }
    });

    // Click retry
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    expect(screen.getByRole('heading', { name: 'Python Basics' })).toBeInTheDocument();
  });

  test('progress tracking updates correctly', async () => {
    render(<LessonViewer userId="user123" subject="python" />);

    await waitFor(() => {
      expect(screen.getByText('Course Progress')).toBeInTheDocument();
    });

    // Initial progress should be shown
    await waitFor(() => {
      expect(screen.getByText('Overall Progress')).toBeInTheDocument();
    });

    // Complete first lesson
    const completeButton = screen.getByText('Mark as Complete');
    fireEvent.click(completeButton);

    await waitFor(() => {
      expect(screen.getByText('Lesson completed!')).toBeInTheDocument();
    });

    // Navigate to next lesson
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Control Flow' })).toBeInTheDocument();
    });

    // Progress should update to show lesson 2 of 3
    expect(screen.getByText('Lesson 2 of 3')).toBeInTheDocument();
  });

  test('handles empty lesson content gracefully', async () => {
    LessonService.getLesson.mockResolvedValue({
      success: true,
      lesson: {
        lesson_number: 1,
        title: 'Empty Lesson',
        content: ''
      }
    });

    render(<LessonViewer userId="user123" subject="python" />);

    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    expect(screen.getByRole('heading', { name: 'Empty Lesson' })).toBeInTheDocument();
    expect(screen.getByText('Mark as Complete')).toBeInTheDocument();
  });

  test('handles quiz content rendering', async () => {
    LessonService.getLesson.mockResolvedValue({
      success: true,
      lesson: {
        lesson_number: 1,
        title: 'Quiz Lesson',
        content: '# Quiz Lesson\n\n```quiz\nWhat is Python?\nA) A snake\nB) A programming language\nC) A movie\n```\n\nMore content here.'
      }
    });

    render(<LessonViewer userId="user123" subject="python" />);

    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    // Quiz content should be processed and rendered
    const markdownContent = screen.getByTestId('markdown-content');
    expect(markdownContent).toHaveTextContent('quiz');
    expect(markdownContent).toHaveTextContent('What is Python?');
  });
});