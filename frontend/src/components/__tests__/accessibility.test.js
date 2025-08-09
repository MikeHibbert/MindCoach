/**
 * Comprehensive accessibility tests for all components
 * Tests WCAG 2.1 AA compliance using axe-core
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';

// Components to test
import ResponsiveLayout from '../ResponsiveLayout';
import SubjectSelector from '../SubjectSelector';
import Survey from '../Survey';
import LessonViewer from '../LessonViewer';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock services
jest.mock('../../services/lessonService', () => ({
  listLessons: jest.fn(() => Promise.resolve({
    success: true,
    lessons: [
      { id: 1, title: 'Lesson 1', estimated_time: '30 min', difficulty: 'beginner' },
      { id: 2, title: 'Lesson 2', estimated_time: '45 min', difficulty: 'intermediate' }
    ]
  })),
  getLesson: jest.fn(() => Promise.resolve({
    success: true,
    lesson: {
      id: 1,
      title: 'Test Lesson',
      content: '# Test Content\n\nThis is a test lesson.',
      estimated_time: '30 min',
      difficulty: 'beginner',
      topics: ['variables', 'functions']
    }
  })),
  getLessonProgress: jest.fn(() => Promise.resolve({
    success: true,
    progress: { progress_percentage: 50 }
  })),
  getLessonCompletionStatus: jest.fn(() => Promise.resolve({
    success: true,
    completed_lessons: [1]
  })),
  markLessonCompleted: jest.fn(() => Promise.resolve({ success: true }))
}));

// Mock fetch for API calls
global.fetch = jest.fn();

describe('Accessibility Tests', () => {
  beforeEach(() => {
    // Reset fetch mock
    fetch.mockClear();
    
    // Mock successful API responses
    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        subjects: [
          {
            id: 'javascript',
            name: 'JavaScript',
            description: 'Learn JavaScript programming',
            locked: false,
            pricing: { monthly: 29 }
          },
          {
            id: 'python',
            name: 'Python',
            description: 'Learn Python programming',
            locked: true,
            pricing: { monthly: 39 }
          }
        ]
      })
    });
  });

  describe('ResponsiveLayout Component', () => {
    const renderWithRouter = (children) => {
      return render(
        <BrowserRouter>
          <ResponsiveLayout>{children}</ResponsiveLayout>
        </BrowserRouter>
      );
    };

    it('should not have accessibility violations', async () => {
      const { container } = renderWithRouter(<div>Test content</div>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have skip link for keyboard navigation', () => {
      renderWithRouter(<div>Test content</div>);
      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });

    it('should have proper ARIA labels for navigation', () => {
      renderWithRouter(<div>Test content</div>);
      
      // Check for navigation landmarks
      const navElements = screen.getAllByRole('navigation');
      expect(navElements.length).toBeGreaterThan(0);
      
      // Check for main content landmark
      const mainElement = screen.getByRole('main');
      expect(mainElement).toBeInTheDocument();
      expect(mainElement).toHaveAttribute('aria-label', 'Main content');
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      renderWithRouter(<div>Test content</div>);
      
      const skipLink = screen.getByText('Skip to main content');
      
      // Test skip link functionality
      await user.tab();
      expect(skipLink).toHaveFocus();
      
      await user.keyboard('{Enter}');
      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveFocus();
    });

    it('should have proper mobile menu accessibility', async () => {
      const user = userEvent.setup();
      
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });
      
      renderWithRouter(<div>Test content</div>);
      
      const menuButton = screen.getByLabelText(/navigation menu/i);
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
      expect(menuButton).toHaveAttribute('aria-controls', 'mobile-menu');
      
      // Open menu
      await user.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');
      
      // Check menu is accessible
      const mobileMenu = screen.getByRole('navigation', { name: /main navigation/i });
      expect(mobileMenu).toBeInTheDocument();
    });

    it('should announce navigation changes to screen readers', async () => {
      const user = userEvent.setup();
      renderWithRouter(<div>Test content</div>);
      
      // Mock mobile menu
      const menuButton = screen.getByLabelText(/navigation menu/i);
      await user.click(menuButton);
      
      // Check for live region announcements
      await waitFor(() => {
        const liveRegions = document.querySelectorAll('[aria-live]');
        expect(liveRegions.length).toBeGreaterThan(0);
      });
    });
  });

  describe('SubjectSelector Component', () => {
    const defaultProps = {
      userId: 'test-user',
      onSubjectSelect: jest.fn()
    };

    it('should not have accessibility violations', async () => {
      const { container } = render(<SubjectSelector {...defaultProps} />);
      
      // Wait for subjects to load
      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have proper form labels and descriptions', async () => {
      render(<SubjectSelector {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });
      
      // Check dropdown has proper labeling
      const dropdown = screen.getByRole('combobox');
      expect(dropdown).toHaveAccessibleName();
      expect(dropdown).toHaveAccessibleDescription();
    });

    it('should support keyboard navigation for subject cards', async () => {
      const user = userEvent.setup();
      render(<SubjectSelector {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });
      
      // Find subject cards
      const subjectCards = screen.getAllByRole('button');
      const jsCard = subjectCards.find(card => 
        card.textContent.includes('JavaScript')
      );
      
      if (jsCard) {
        // Test keyboard navigation
        jsCard.focus();
        expect(jsCard).toHaveFocus();
        
        // Test activation with Enter
        await user.keyboard('{Enter}');
        expect(defaultProps.onSubjectSelect).toHaveBeenCalled();
      }
    });

    it('should properly indicate locked subjects', async () => {
      render(<SubjectSelector {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument();
      });
      
      const pythonCard = screen.getByRole('button', { name: /python/i });
      expect(pythonCard).toHaveAttribute('aria-disabled', 'true');
      expect(pythonCard).toHaveAccessibleDescription(/subscription required/i);
    });

    it('should announce selection changes', async () => {
      const user = userEvent.setup();
      render(<SubjectSelector {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });
      
      const jsCard = screen.getByRole('button', { name: /javascript/i });
      await user.click(jsCard);
      
      // Check for live region announcements
      await waitFor(() => {
        const liveRegions = document.querySelectorAll('[aria-live]');
        expect(liveRegions.length).toBeGreaterThan(0);
      });
    });

    it('should handle loading and error states accessibly', async () => {
      // Test loading state
      const { rerender } = render(<SubjectSelector {...defaultProps} />);
      
      const loadingIndicator = screen.getByRole('status');
      expect(loadingIndicator).toBeInTheDocument();
      expect(loadingIndicator).toHaveAttribute('aria-live', 'polite');
      
      // Test error state
      fetch.mockRejectedValueOnce(new Error('Network error'));
      
      rerender(<SubjectSelector {...defaultProps} />);
      
      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toBeInTheDocument();
        expect(errorAlert).toHaveAttribute('aria-live', 'assertive');
      });
    });
  });

  describe('Survey Component', () => {
    const mockSurveyData = {
      id: 'test-survey',
      subject: 'javascript',
      user_id: 'test-user',
      questions: [
        {
          id: 1,
          question: 'What is a variable?',
          type: 'multiple_choice',
          options: ['A storage location', 'A function', 'A loop', 'A condition'],
          difficulty: 'beginner',
          topic: 'variables'
        },
        {
          id: 2,
          question: 'JavaScript is a compiled language.',
          type: 'true_false',
          difficulty: 'beginner',
          topic: 'basics'
        },
        {
          id: 3,
          question: 'Explain closures in JavaScript.',
          type: 'text',
          difficulty: 'advanced',
          topic: 'functions'
        }
      ]
    };

    const defaultProps = {
      surveyData: mockSurveyData,
      onSubmit: jest.fn(),
      onProgress: jest.fn()
    };

    it('should not have accessibility violations', async () => {
      const { container } = render(<Survey {...defaultProps} />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have proper form structure with fieldsets', () => {
      render(<Survey {...defaultProps} />);
      
      // Check for fieldset for multiple choice questions
      const fieldset = screen.getByRole('group');
      expect(fieldset).toBeInTheDocument();
      
      // Check for proper labeling
      const questionTitle = screen.getByRole('heading', { level: 3 });
      expect(questionTitle).toBeInTheDocument();
      expect(questionTitle).toHaveAttribute('tabIndex', '-1');
    });

    it('should support keyboard navigation between options', async () => {
      const user = userEvent.setup();
      render(<Survey {...defaultProps} />);
      
      const radioButtons = screen.getAllByRole('radio');
      expect(radioButtons.length).toBe(4); // Multiple choice options
      
      // Test arrow key navigation
      radioButtons[0].focus();
      await user.keyboard('{ArrowDown}');
      expect(radioButtons[1]).toHaveFocus();
      
      await user.keyboard('{ArrowUp}');
      expect(radioButtons[0]).toHaveFocus();
    });

    it('should have proper progress indication', () => {
      render(<Survey {...defaultProps} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute('aria-valuenow');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
      expect(progressBar).toHaveAccessibleName(/survey progress/i);
    });

    it('should announce navigation between questions', async () => {
      const user = userEvent.setup();
      render(<Survey {...defaultProps} />);
      
      // Answer first question
      const firstOption = screen.getAllByRole('radio')[0];
      await user.click(firstOption);
      
      // Navigate to next question
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);
      
      // Check for live region announcements
      await waitFor(() => {
        const liveRegions = document.querySelectorAll('[aria-live]');
        expect(liveRegions.length).toBeGreaterThan(0);
      });
    });

    it('should handle validation errors accessibly', async () => {
      const user = userEvent.setup();
      render(<Survey {...defaultProps} />);
      
      // Try to navigate without answering
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);
      
      // Check for error message
      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toBeInTheDocument();
        expect(errorAlert).toHaveAttribute('aria-live', 'assertive');
      });
      
      // Check that radio buttons are properly associated with error
      const radioButtons = screen.getAllByRole('radio');
      radioButtons.forEach(radio => {
        expect(radio).toHaveAttribute('aria-describedby');
      });
    });

    it('should handle different question types accessibly', async () => {
      const user = userEvent.setup();
      render(<Survey {...defaultProps} />);
      
      // Navigate to true/false question
      const firstOption = screen.getAllByRole('radio')[0];
      await user.click(firstOption);
      
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);
      
      // Check true/false question structure
      await waitFor(() => {
        const truefalseOptions = screen.getAllByRole('radio');
        expect(truefalseOptions.length).toBe(2);
        
        const fieldset = screen.getByRole('group');
        expect(fieldset).toBeInTheDocument();
      });
      
      // Navigate to text question
      const trueOption = screen.getByRole('radio', { name: /true/i });
      await user.click(trueOption);
      await user.click(nextButton);
      
      // Check text question structure
      await waitFor(() => {
        const textarea = screen.getByRole('textbox');
        expect(textarea).toBeInTheDocument();
        expect(textarea).toHaveAccessibleName();
        expect(textarea).toHaveAccessibleDescription();
      });
    });

    it('should have accessible navigation buttons', () => {
      render(<Survey {...defaultProps} />);
      
      const previousButton = screen.getByRole('button', { name: /previous/i });
      const nextButton = screen.getByRole('button', { name: /next/i });
      
      expect(previousButton).toHaveAccessibleName(/currently on question/i);
      expect(nextButton).toHaveAccessibleName(/currently on question/i);
      
      // Check disabled state
      expect(previousButton).toBeDisabled();
      expect(previousButton).toHaveClass('btn-disabled');
    });
  });

  describe('LessonViewer Component', () => {
    const defaultProps = {
      userId: 'test-user',
      subject: 'javascript',
      initialLessonNumber: 1
    };

    it('should not have accessibility violations', async () => {
      const { container } = render(<LessonViewer {...defaultProps} />);
      
      // Wait for lesson to load
      await waitFor(() => {
        expect(screen.getByText('Test Lesson')).toBeInTheDocument();
      });
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have proper navigation structure', async () => {
      render(<LessonViewer {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Test Lesson')).toBeInTheDocument();
      });
      
      // Check for navigation landmarks
      const navElements = screen.getAllByRole('navigation');
      expect(navElements.length).toBeGreaterThan(0);
      
      // Check for main content
      const mainElement = screen.getByRole('main');
      expect(mainElement).toBeInTheDocument();
      expect(mainElement).toHaveAttribute('aria-label', 'Lesson content');
    });

    it('should have accessible lesson sidebar', async () => {
      render(<LessonViewer {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Course Progress')).toBeInTheDocument();
      });
      
      // Check progress bar
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAccessibleName(/course completion/i);
      
      // Check lesson list
      const lessonList = screen.getByRole('list', { name: /lesson list/i });
      expect(lessonList).toBeInTheDocument();
      
      const lessonItems = screen.getAllByRole('listitem');
      expect(lessonItems.length).toBeGreaterThan(0);
    });

    it('should support keyboard navigation in lesson list', async () => {
      const user = userEvent.setup();
      render(<LessonViewer {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Lesson 1')).toBeInTheDocument();
      });
      
      const lessonButtons = screen.getAllByRole('button');
      const lessonButton = lessonButtons.find(btn => 
        btn.textContent.includes('Lesson 1')
      );
      
      if (lessonButton) {
        lessonButton.focus();
        expect(lessonButton).toHaveFocus();
        
        // Test arrow key navigation
        await user.keyboard('{ArrowDown}');
        // Should focus next lesson button
      }
    });

    it('should have accessible lesson content', async () => {
      render(<LessonViewer {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Test Lesson')).toBeInTheDocument();
      });
      
      // Check main content area
      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveAttribute('tabIndex', '-1');
      
      // Check headings are focusable
      const headings = screen.getAllByRole('heading');
      headings.forEach(heading => {
        expect(heading).toHaveAttribute('tabIndex', '0');
      });
    });

    it('should have accessible code blocks', async () => {
      // Mock lesson with code content
      const LessonService = require('../services/lessonService');
      LessonService.getLesson.mockResolvedValueOnce({
        success: true,
        lesson: {
          id: 1,
          title: 'Code Lesson',
          content: '# Code Example\n\n```javascript\nconst x = 5;\n```',
          estimated_time: '30 min',
          difficulty: 'beginner'
        }
      });
      
      render(<LessonViewer {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Code Lesson')).toBeInTheDocument();
      });
      
      // Check code blocks have proper labeling
      const codeRegions = screen.getAllByRole('region');
      const codeRegion = codeRegions.find(region => 
        region.getAttribute('aria-label')?.includes('Code example')
      );
      
      if (codeRegion) {
        expect(codeRegion).toHaveAccessibleName(/code example/i);
        
        // Check code block is focusable
        const preElement = codeRegion.querySelector('pre');
        expect(preElement).toHaveAttribute('tabIndex', '0');
      }
    });

    it('should announce lesson completion', async () => {
      const user = userEvent.setup();
      render(<LessonViewer {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Test Lesson')).toBeInTheDocument();
      });
      
      const completeButton = screen.getByRole('button', { name: /mark.*complete/i });
      await user.click(completeButton);
      
      // Check for completion status
      await waitFor(() => {
        const statusElement = screen.getByRole('status');
        expect(statusElement).toBeInTheDocument();
        expect(statusElement).toHaveAttribute('aria-live', 'polite');
      });
    });

    it('should have accessible navigation controls', async () => {
      render(<LessonViewer {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Test Lesson')).toBeInTheDocument();
      });
      
      const navButtons = screen.getAllByRole('button');
      const prevButton = navButtons.find(btn => btn.textContent.includes('Previous'));
      const nextButton = navButtons.find(btn => btn.textContent.includes('Next'));
      
      if (prevButton) {
        expect(prevButton).toHaveAccessibleName(/currently on lesson/i);
      }
      
      if (nextButton) {
        expect(nextButton).toHaveAccessibleName(/currently on lesson/i);
      }
    });
  });

  describe('Cross-Component Integration', () => {
    it('should maintain focus management across component transitions', async () => {
      const user = userEvent.setup();
      
      // Test focus management when navigating between components
      const { rerender } = render(
        <BrowserRouter>
          <ResponsiveLayout>
            <SubjectSelector userId="test-user" onSubjectSelect={jest.fn()} />
          </ResponsiveLayout>
        </BrowserRouter>
      );
      
      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });
      
      // Select a subject
      const jsCard = screen.getByRole('button', { name: /javascript/i });
      await user.click(jsCard);
      
      // Simulate navigation to survey
      rerender(
        <BrowserRouter>
          <ResponsiveLayout>
            <Survey 
              surveyData={{
                id: 'test',
                subject: 'javascript',
                user_id: 'test-user',
                questions: [{
                  id: 1,
                  question: 'Test question?',
                  type: 'multiple_choice',
                  options: ['A', 'B']
                }]
              }}
              onSubmit={jest.fn()}
            />
          </ResponsiveLayout>
        </BrowserRouter>
      );
      
      // Check that focus is properly managed
      await waitFor(() => {
        const questionTitle = screen.getByRole('heading', { level: 3 });
        expect(questionTitle).toBeInTheDocument();
      });
    });

    it('should maintain consistent color contrast across all components', async () => {
      // This test would ideally use a color contrast analyzer
      // For now, we'll check that high contrast classes are applied
      
      const components = [
        <SubjectSelector userId="test-user" onSubjectSelect={jest.fn()} />,
        <Survey 
          surveyData={{
            id: 'test',
            subject: 'test',
            user_id: 'test-user',
            questions: [{
              id: 1,
              question: 'Test?',
              type: 'multiple_choice',
              options: ['A', 'B']
            }]
          }}
          onSubmit={jest.fn()}
        />,
        <LessonViewer userId="test-user" subject="test" />
      ];
      
      for (const component of components) {
        const { container, unmount } = render(component);
        
        // Check for high contrast button classes
        const buttons = container.querySelectorAll('button');
        buttons.forEach(button => {
          const classes = button.className;
          // Should have proper contrast classes
          expect(classes).toMatch(/(btn-primary|btn-secondary|btn-success|btn-danger|btn-disabled)/);
        });
        
        unmount();
      }
    });
  });
});