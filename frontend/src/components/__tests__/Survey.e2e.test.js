import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import SurveyContainer from '../SurveyContainer';
import SurveyResults from '../SurveyResults';
import SurveyService from '../../services/surveyService';

// Mock the SurveyService
jest.mock('../../services/surveyService');

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock survey data for complete workflow
const mockSurveyData = {
  id: 'survey-123',
  subject: 'python',
  subject_name: 'Python Programming',
  user_id: 'test-user-123',
  questions: [
    {
      id: 1,
      question: 'What is the correct way to create a list in Python?',
      type: 'multiple_choice',
      options: [
        'list = []',
        'list = {}',
        'list = ()',
        'list = ""'
      ],
      difficulty: 'beginner',
      topic: 'data_structures'
    },
    {
      id: 2,
      question: 'Python supports object-oriented programming.',
      type: 'true_false',
      difficulty: 'beginner',
      topic: 'concepts'
    },
    {
      id: 3,
      question: 'Explain the difference between a list and a tuple.',
      type: 'text',
      difficulty: 'intermediate',
      topic: 'data_structures'
    }
  ],
  metadata: {
    topics_covered: ['data_structures', 'concepts']
  },
  generated_at: '2024-01-15T10:00:00Z'
};

const mockSurveyResults = {
  user_id: 'test-user-123',
  subject: 'python',
  skill_level: 'intermediate',
  accuracy: 67,
  total_questions: 3,
  correct_answers: 2,
  topic_analysis: {
    data_structures: {
      correct: 2,
      total: 2,
      accuracy: 100
    },
    concepts: {
      correct: 0,
      total: 1,
      accuracy: 0
    }
  },
  recommendations: [
    'Focus on object-oriented programming concepts',
    'Practice more with Python classes and inheritance',
    'Review basic OOP principles'
  ],
  processed_at: '2024-01-15T10:30:00Z'
};

describe('Survey End-to-End Workflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
  });

  const renderSurveyContainer = (userId = 'test-user-123', subject = 'python') => {
    // Mock useParams for SurveyContainer
    jest.doMock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate,
      useParams: () => ({ userId, subject })
    }));

    return render(
      <MemoryRouter initialEntries={[`/users/${userId}/subjects/${subject}/survey`]}>
        <SurveyContainer />
      </MemoryRouter>
    );
  };

  const renderSurveyResults = (userId = 'test-user-123', subject = 'python', results = null) => {
    // Mock useParams and useLocation for SurveyResults
    jest.doMock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate,
      useParams: () => ({ userId, subject }),
      useLocation: () => ({
        state: results ? { surveyResults: results } : null
      })
    }));

    return render(
      <MemoryRouter initialEntries={[`/users/${userId}/subjects/${subject}/results`]}>
        <SurveyResults />
      </MemoryRouter>
    );
  };

  describe('Complete Survey Workflow', () => {
    test('completes full survey workflow from start to results', async () => {
      // Setup mocks
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.submitSurvey.mockResolvedValue(mockSurveyResults);
      SurveyService.validateSurveyData.mockReturnValue(true);

      const user = userEvent.setup();
      renderSurveyContainer();

      // 1. Survey loads
      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Verify initial state
      expect(screen.getByText('Question 1 of 3 • 0 answered')).toBeInTheDocument();
      expect(screen.getByText('33%')).toBeInTheDocument();

      // 2. Answer first question (multiple choice)
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      
      // Progress should update
      await waitFor(() => {
        expect(screen.getByText('Question 1 of 3 • 1 answered')).toBeInTheDocument();
      });

      // Navigate to next question
      await user.click(screen.getByRole('button', { name: /Next/ }));

      // 3. Answer second question (true/false)
      expect(screen.getByText('Question 2 of 3')).toBeInTheDocument();
      expect(screen.getByText('Python supports object-oriented programming.')).toBeInTheDocument();
      
      await user.click(screen.getByLabelText('False')); // Intentionally wrong answer
      await user.click(screen.getByRole('button', { name: /Next/ }));

      // 4. Answer third question (text)
      expect(screen.getByText('Question 3 of 3')).toBeInTheDocument();
      expect(screen.getByText('Explain the difference between a list and a tuple.')).toBeInTheDocument();
      
      const textArea = screen.getByRole('textbox');
      await user.type(textArea, 'Lists are mutable and can be changed after creation, while tuples are immutable and cannot be modified.');

      // 5. Submit survey
      expect(screen.getByRole('button', { name: /Submit Survey/ })).toBeInTheDocument();
      await user.click(screen.getByRole('button', { name: /Submit Survey/ }));

      // 6. Verify submission
      await waitFor(() => {
        expect(SurveyService.submitSurvey).toHaveBeenCalledWith(
          'test-user-123',
          'python',
          expect.objectContaining({
            survey_id: 'survey-123',
            user_id: 'test-user-123',
            subject: 'python',
            answers: [
              expect.objectContaining({
                question_id: 1,
                answer: 0,
                question_text: 'What is the correct way to create a list in Python?',
                question_type: 'multiple_choice'
              }),
              expect.objectContaining({
                question_id: 2,
                answer: 1,
                question_text: 'Python supports object-oriented programming.',
                question_type: 'true_false'
              }),
              expect.objectContaining({
                question_id: 3,
                answer: 'Lists are mutable and can be changed after creation, while tuples are immutable and cannot be modified.',
                question_text: 'Explain the difference between a list and a tuple.',
                question_type: 'text'
              })
            ]
          })
        );
      });

      // 7. Navigation to results
      expect(mockNavigate).toHaveBeenCalledWith(
        '/users/test-user-123/subjects/python/results',
        {
          state: {
            surveyResults: mockSurveyResults,
            subject: 'python',
            userId: 'test-user-123'
          }
        }
      );
    });

    test('handles survey validation errors during workflow', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      const user = userEvent.setup();
      renderSurveyContainer();

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Try to proceed without answering
      await user.click(screen.getByRole('button', { name: /Next/ }));

      // Should show validation error
      expect(screen.getByText('Please select an answer before continuing.')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();

      // Answer the question
      await user.click(screen.getByRole('radio', { name: 'list = []' }));

      // Error should clear
      expect(screen.queryByText('Please select an answer before continuing.')).not.toBeInTheDocument();

      // Should be able to proceed
      await user.click(screen.getByRole('button', { name: /Next/ }));
      expect(screen.getByText('Question 2 of 3')).toBeInTheDocument();
    });

    test('handles incomplete survey submission', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      const user = userEvent.setup();
      renderSurveyContainer();

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Answer only first question
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));

      // Skip second question, go to third
      await user.click(screen.getByRole('button', { name: /Next/ }));

      // Answer third question
      await user.type(screen.getByRole('textbox'), 'Some answer');

      // Try to submit with missing answer
      await user.click(screen.getByRole('button', { name: /Submit Survey/ }));

      // Should not submit and should navigate back to unanswered question
      expect(SurveyService.submitSurvey).not.toHaveBeenCalled();
      
      await waitFor(() => {
        expect(screen.getByText('Question 2 of 3')).toBeInTheDocument();
      });
    });
  });

  describe('Survey Results Display', () => {
    test('displays survey results correctly', async () => {
      const { SurveyResults: TestSurveyResults } = await import('../SurveyResults');
      
      render(
        <MemoryRouter>
          <TestSurveyResults />
        </MemoryRouter>
      );

      // Mock the hooks for this specific test
      jest.doMock('react-router-dom', () => ({
        ...jest.requireActual('react-router-dom'),
        useNavigate: () => mockNavigate,
        useParams: () => ({ userId: 'test-user-123', subject: 'python' }),
        useLocation: () => ({
          state: { surveyResults: mockSurveyResults }
        })
      }));

      // Re-render with mocked hooks
      const { rerender } = render(
        <MemoryRouter>
          <TestSurveyResults />
        </MemoryRouter>
      );

      // Check results display
      expect(screen.getByText('Assessment Complete! 🎉')).toBeInTheDocument();
      expect(screen.getByText('Intermediate')).toBeInTheDocument();
      expect(screen.getByText('67%')).toBeInTheDocument();
      expect(screen.getByText('2/3')).toBeInTheDocument();
    });

    test('handles results navigation actions', async () => {
      const { SurveyResults: TestSurveyResults } = await import('../SurveyResults');
      
      jest.doMock('react-router-dom', () => ({
        ...jest.requireActual('react-router-dom'),
        useNavigate: () => mockNavigate,
        useParams: () => ({ userId: 'test-user-123', subject: 'python' }),
        useLocation: () => ({
          state: { surveyResults: mockSurveyResults }
        })
      }));

      const user = userEvent.setup();
      render(
        <MemoryRouter>
          <TestSurveyResults />
        </MemoryRouter>
      );

      // Test start learning action
      const startLearningButton = screen.getByRole('button', { name: /Start Learning Path/ });
      await user.click(startLearningButton);

      expect(mockNavigate).toHaveBeenCalledWith('/users/test-user-123/subjects/python/lessons');

      // Test retake survey action
      mockNavigate.mockClear();
      const retakeButton = screen.getByRole('button', { name: /Retake Assessment/ });
      await user.click(retakeButton);

      expect(mockNavigate).toHaveBeenCalledWith('/users/test-user-123/subjects/python/survey');
    });
  });

  describe('Error Recovery Workflows', () => {
    test('recovers from network errors during survey loading', async () => {
      // First call fails, second succeeds
      SurveyService.getOrGenerateSurvey
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      const user = userEvent.setup();
      renderSurveyContainer();

      // Should show error
      await waitFor(() => {
        expect(screen.getByText('⚠️ Error Loading Survey')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      // Retry should work
      await user.click(screen.getByRole('button', { name: 'Retry' }));

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      expect(SurveyService.getOrGenerateSurvey).toHaveBeenCalledTimes(2);
    });

    test('recovers from submission errors', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);
      
      // First submission fails, second succeeds
      SurveyService.submitSurvey
        .mockRejectedValueOnce(new Error('Submission failed'))
        .mockResolvedValueOnce(mockSurveyResults);

      const user = userEvent.setup();
      renderSurveyContainer();

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Answer all questions
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.click(screen.getByLabelText('True'));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.type(screen.getByRole('textbox'), 'Test answer');

      // First submission attempt
      await user.click(screen.getByRole('button', { name: /Submit Survey/ }));

      // Should show error
      await waitFor(() => {
        expect(screen.getByText('Submission failed')).toBeInTheDocument();
      });

      // Retry submission
      await user.click(screen.getByRole('button', { name: /Submit Survey/ }));

      // Should succeed
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(
          '/users/test-user-123/subjects/python/results',
          expect.any(Object)
        );
      });
    });
  });

  describe('Accessibility in Workflow', () => {
    test('maintains accessibility throughout survey workflow', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      const user = userEvent.setup();
      renderSurveyContainer();

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Check progress bar accessibility
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-label', 'Survey progress: 33% complete');

      // Check form accessibility
      const radioButtons = screen.getAllByRole('radio');
      expect(radioButtons[0]).toHaveAttribute('name', 'question-1');

      // Test keyboard navigation
      await user.tab();
      expect(radioButtons[0]).toHaveFocus();

      await user.tab();
      expect(radioButtons[1]).toHaveFocus();

      // Test error message accessibility
      await user.click(screen.getByRole('button', { name: /Next/ }));
      
      const errorMessage = screen.getByRole('alert');
      expect(errorMessage).toBeInTheDocument();
      expect(radioButtons[0]).toHaveAttribute('aria-describedby', 'error-1');
    });
  });

  describe('Responsive Behavior in Workflow', () => {
    test('maintains responsive design throughout workflow', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      renderSurveyContainer();

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Check mobile-specific classes
      const options = screen.getAllByRole('radio').map(radio => radio.closest('label'));
      options.forEach(option => {
        expect(option).toHaveClass('mobile:min-h-[56px]');
        expect(option).toHaveClass('tablet:min-h-[60px]');
      });

      // Check button touch targets
      const nextButton = screen.getByRole('button', { name: /Next/ });
      expect(nextButton).toHaveClass('mobile:min-h-[44px]');
      expect(nextButton).toHaveClass('tablet:min-h-[48px]');
    });
  });
});