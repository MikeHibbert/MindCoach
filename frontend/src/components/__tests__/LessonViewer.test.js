import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import LessonViewer from '../LessonViewer';
import LessonService from '../../services/lessonService';

// Mock the LessonService
jest.mock('../../services/lessonService');

// Mock ReactMarkdown and related modules to avoid complex rendering in tests
jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }) {
    return <div data-testid="markdown-content">{children}</div>;
  };
});

jest.mock('remark-gfm', () => ({}));
jest.mock('rehype-highlight', () => ({}));

const mockLessons = [
  {
    lesson_number: 1,
    title: 'Introduction to Python',
    estimated_time: '30 minutes',
    difficulty: 'beginner',
    topics: ['variables', 'data types']
  },
  {
    lesson_number: 2,
    title: 'Control Structures',
    estimated_time: '45 minutes',
    difficulty: 'intermediate',
    topics: ['if statements', 'loops']
  }
];

const mockLesson = {
  lesson_number: 1,
  title: 'Introduction to Python',
  estimated_time: '30 minutes',
  difficulty: 'beginner',
  topics: ['variables', 'data types'],
  content: '# Introduction to Python\n\nThis is a lesson about Python basics.\n\n```python\nprint("Hello, World!")\n```'
};

const mockProgress = {
  user_id: 'user123',
  subject: 'python',
  total_lessons_generated: 2,
  available_lessons: 2,
  progress_percentage: 50.0,
  skill_level: 'beginner'
};

describe('LessonViewer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
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
    LessonService.getLessonCompletionStatus.mockResolvedValue({
      success: true,
      completed_lessons: []
    });
    LessonService.markLessonCompleted.mockResolvedValue({
      success: true,
      message: 'Lesson marked as completed'
    });
  });

  test('renders loading state initially', () => {
    render(<LessonViewer userId="user123" subject="python" />);
    
    expect(screen.getByText('Loading lesson...')).toBeInTheDocument();
  });

  test('renders lesson content after loading', async () => {
    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
    
    expect(screen.getByText('30 minutes')).toBeInTheDocument();
    expect(screen.getByText('beginner')).toBeInTheDocument();
    expect(screen.getByText('variables')).toBeInTheDocument();
    expect(screen.getByText('data types')).toBeInTheDocument();
  });

  test('renders lesson navigation', async () => {
    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByText('Introduction to Python')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
    expect(screen.getByText('Lesson 1 of 2')).toBeInTheDocument();
  });

  test('disables previous button on first lesson', async () => {
    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
    
    const previousButton = screen.getByText('Previous').closest('button');
    expect(previousButton).toBeDisabled();
  });

  test('enables next button when not on last lesson', async () => {
    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
    
    const nextButton = screen.getByText('Next').closest('button');
    expect(nextButton).not.toBeDisabled();
  });

  test('navigates to next lesson when next button is clicked', async () => {
    const mockLesson2 = {
      ...mockLesson,
      lesson_number: 2,
      title: 'Control Structures'
    };
    
    LessonService.getLesson.mockImplementation((userId, subject, lessonNumber) => {
      if (lessonNumber === 1) {
        return Promise.resolve({ success: true, lesson: mockLesson });
      } else if (lessonNumber === 2) {
        return Promise.resolve({ success: true, lesson: mockLesson2 });
      }
    });

    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
    
    const nextButton = screen.getByText('Next').closest('button');
    fireEvent.click(nextButton);
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Control Structures' })).toBeInTheDocument();
    });
    
    expect(screen.getByText('Lesson 2 of 2')).toBeInTheDocument();
  });

  test('renders lesson sidebar with progress', async () => {
    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByText('Course Progress')).toBeInTheDocument();
    });
    
    await waitFor(() => {
      expect(screen.getByText('Overall Progress')).toBeInTheDocument();
    });
    
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  test('renders lesson list in sidebar', async () => {
    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByText('Course Progress')).toBeInTheDocument();
    });
    
    await waitFor(() => {
      expect(screen.getByText('Control Structures')).toBeInTheDocument();
    });
    
    // Check if lesson titles appear in sidebar
    const lessonButtons = screen.getAllByText('Introduction to Python');
    expect(lessonButtons.length).toBeGreaterThan(1); // One in main content, one in sidebar
  });

  test('handles lesson loading error', async () => {
    LessonService.getLesson.mockRejectedValue(new Error('Failed to load lesson'));
    
    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading lesson')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Failed to load lesson')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  test('handles missing userId or subject', () => {
    render(<LessonViewer />);
    
    expect(screen.getByText('Please select a subject to view lessons.')).toBeInTheDocument();
  });

  test('caches loaded lessons', async () => {
    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
    
    // Navigate to next lesson and back
    const nextButton = screen.getByText('Next').closest('button');
    fireEvent.click(nextButton);
    
    await waitFor(() => {
      expect(LessonService.getLesson).toHaveBeenCalledWith('user123', 'python', 2);
    });
    
    const previousButton = screen.getByText('Previous').closest('button');
    fireEvent.click(previousButton);
    
    // Should not call API again for cached lesson
    expect(LessonService.getLesson).toHaveBeenCalledTimes(2); // Initial load + lesson 2
  });

  test('renders markdown content', async () => {
    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
  });

  test('handles responsive design with mobile lesson selector', async () => {
    // Mock window.innerWidth for mobile
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
    
    // Check for mobile lesson selector (select element)
    const mobileSelector = screen.getByDisplayValue('Lesson 1: Introduction to Python');
    expect(mobileSelector).toBeInTheDocument();
  });

  test('handles quiz content rendering', async () => {
    const lessonWithQuiz = {
      ...mockLesson,
      content: '# Lesson\n\n```quiz\nWhat is Python?\nA) A snake\nB) A programming language\n```'
    };
    
    LessonService.getLesson.mockResolvedValue({
      success: true,
      lesson: lessonWithQuiz
    });

    render(<LessonViewer userId="user123" subject="python" />);
    
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
    
    // The quiz content should be processed and rendered
    expect(screen.getByTestId('markdown-content')).toHaveTextContent('quiz');
  });
});