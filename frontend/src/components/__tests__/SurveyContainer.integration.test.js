import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import SurveyContainer from '../SurveyContainer';
import SurveyService from '../../services/surveyService';

// Mock the SurveyService
jest.mock('../../services/surveyService');

// Mock react-router-dom hooks
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({
    userId: 'test-user-123',
    subject: 'python'
  })
}));

// Mock survey data
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
  accuracy: 75,
  total_questions: 2,
  correct_answers: 1,
  topic_analysis: {
    data_structures: {
      correct: 1,
      total: 1,
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
    'Practice more with Python classes and inheritance'
  ],
  processed_at: '2024-01-15T10:30:00Z'
};

describe('SurveyContainer Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
  });

  const renderWithRouter = (component) => {
    return render(
      <MemoryRouter initialEntries={['/users/test-user-123/subjects/python/survey']}>
        {component}
      </MemoryRouter>
    );
  };

  describe('Survey Loading', () => {
    test('loads existing survey on mount', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      renderWithRouter(<SurveyContainer />);

      // Should show loading state initially
      expect(screen.getByText('Loading survey...')).toBeInTheDocument();

      // Wait for survey to load
      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      expect(SurveyService.getOrGenerateSurvey).toHaveBeenCalledWith(
        'test-user-123',
        'python',
        false
      );
    });

    test('generates new survey when existing survey not found', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      renderWithRouter(<SurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      expect(SurveyService.getOrGenerateSurvey).toHaveBeenCalledWith(
        'test-user-123',
        'python',
        false
      );
    });

    test('handles survey loading error', async () => {
      const errorMessage = 'Failed to load survey';
      SurveyService.getOrGenerateSurvey.mockRejectedValue(new Error(errorMessage));

      renderWithRouter(<SurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('⚠️ Error Loading Survey')).toBeInTheDocument();
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Generate New Survey' })).toBeInTheDocument();
    });

    test('validates survey data structure', async () => {
      const invalidSurveyData = { invalid: 'data' };
      SurveyService.getOrGenerateSurvey.mockResolvedValue(invalidSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(false);

      renderWithRouter(<SurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('Invalid survey data received from server')).toBeInTheDocument();
      });
    });
  });

  describe('Survey Submission', () => {
    test('submits survey and navigates to results', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.submitSurvey.mockResolvedValue(mockSurveyResults);
      SurveyService.validateSurveyData.mockReturnValue(true);

      const user = userEvent.setup();
      renderWithRouter(<SurveyContainer />);

      // Wait for survey to load
      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Answer questions
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.click(screen.getByLabelText('True'));

      // Submit survey
      await user.click(screen.getByRole('button', { name: /Submit Survey/ }));

      await waitFor(() => {
        expect(SurveyService.submitSurvey).toHaveBeenCalledWith(
          'test-user-123',
          'python',
          expect.objectContaining({
            survey_id: 'survey-123',
            user_id: 'test-user-123',
            subject: 'python',
            answers: expect.arrayContaining([
              expect.objectContaining({
                question_id: 1,
                answer: 0
              }),
              expect.objectContaining({
                question_id: 2,
                answer: 0
              })
            ])
          })
        );
      });

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

    test('handles survey submission error', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);
      const errorMessage = 'Failed to submit survey';
      SurveyService.submitSurvey.mockRejectedValue(new Error(errorMessage));

      const user = userEvent.setup();
      renderWithRouter(<SurveyContainer />);

      // Wait for survey to load
      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Answer questions
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.click(screen.getByLabelText('True'));

      // Submit survey
      await user.click(screen.getByRole('button', { name: /Submit Survey/ }));

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      expect(mockNavigate).not.toHaveBeenCalled();
    });

    test('shows loading state during submission', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);
      
      let resolveSubmit;
      const submitPromise = new Promise(resolve => {
        resolveSubmit = resolve;
      });
      SurveyService.submitSurvey.mockReturnValue(submitPromise);

      const user = userEvent.setup();
      renderWithRouter(<SurveyContainer />);

      // Wait for survey to load
      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Answer questions
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.click(screen.getByLabelText('True'));

      // Submit survey
      await user.click(screen.getByRole('button', { name: /Submit Survey/ }));

      // Should show submitting state
      expect(screen.getByText('Submitting...')).toBeInTheDocument();

      // Resolve submission
      resolveSubmit(mockSurveyResults);
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalled();
      });
    });
  });

  describe('Progress Tracking', () => {
    test('displays progress information', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      renderWithRouter(<SurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Check progress display
      expect(screen.getByText('Question 1 of 2 • 0 answered')).toBeInTheDocument();
      expect(screen.getByText('33%')).toBeInTheDocument();
      expect(screen.getByText('Complete')).toBeInTheDocument();
    });

    test('updates progress when answering questions', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      const user = userEvent.setup();
      renderWithRouter(<SurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Answer first question
      await user.click(screen.getByRole('radio', { name: 'list = []' }));

      // Progress should update
      await waitFor(() => {
        expect(screen.getByText('Question 1 of 2 • 1 answered')).toBeInTheDocument();
        expect(screen.getByText('33%')).toBeInTheDocument();
      });
    });
  });

  describe('Survey Actions', () => {
    test('regenerates survey when requested', async () => {
      SurveyService.getOrGenerateSurvey
        .mockResolvedValueOnce(mockSurveyData)
        .mockResolvedValueOnce({ ...mockSurveyData, id: 'new-survey-456' });
      SurveyService.validateSurveyData.mockReturnValue(true);

      const user = userEvent.setup();
      renderWithRouter(<SurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Click regenerate survey
      await user.click(screen.getByText('Generate New Survey'));

      await waitFor(() => {
        expect(SurveyService.getOrGenerateSurvey).toHaveBeenCalledWith(
          'test-user-123',
          'python',
          true
        );
      });
    });

    test('handles retry after error', async () => {
      SurveyService.getOrGenerateSurvey
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      const user = userEvent.setup();
      renderWithRouter(<SurveyContainer />);

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByText('⚠️ Error Loading Survey')).toBeInTheDocument();
      });

      // Click retry
      await user.click(screen.getByRole('button', { name: 'Retry' }));

      // Should load survey successfully
      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      expect(SurveyService.getOrGenerateSurvey).toHaveBeenCalledTimes(2);
    });

    test('navigates back when go back is clicked', async () => {
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      const user = userEvent.setup();
      renderWithRouter(<SurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      // Click go back
      await user.click(screen.getByText('Go Back'));

      expect(mockNavigate).toHaveBeenCalledWith(-1);
    });
  });

  describe('Error Handling', () => {
    test('handles missing parameters', async () => {
      // Mock useParams to return missing parameters
      jest.doMock('react-router-dom', () => ({
        ...jest.requireActual('react-router-dom'),
        useNavigate: () => mockNavigate,
        useParams: () => ({
          userId: null,
          subject: null
        })
      }));

      const { SurveyContainer: TestSurveyContainer } = await import('../SurveyContainer');
      
      renderWithRouter(<TestSurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('Missing user ID or subject parameter')).toBeInTheDocument();
      });
    });

    test('handles network errors gracefully', async () => {
      SurveyService.getOrGenerateSurvey.mockRejectedValue(new Error('Network error'));

      renderWithRouter(<SurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });
  });

  describe('Development Features', () => {
    const originalEnv = process.env.NODE_ENV;

    afterEach(() => {
      process.env.NODE_ENV = originalEnv;
    });

    test('shows debug info in development mode', async () => {
      process.env.NODE_ENV = 'development';
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      renderWithRouter(<SurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('Debug Info (Development Only)')).toBeInTheDocument();
      });

      // Check debug info content
      expect(screen.getByText('Survey ID:')).toBeInTheDocument();
      expect(screen.getByText('survey-123')).toBeInTheDocument();
    });

    test('hides debug info in production mode', async () => {
      process.env.NODE_ENV = 'production';
      SurveyService.getOrGenerateSurvey.mockResolvedValue(mockSurveyData);
      SurveyService.validateSurveyData.mockReturnValue(true);

      renderWithRouter(<SurveyContainer />);

      await waitFor(() => {
        expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      });

      expect(screen.queryByText('Debug Info (Development Only)')).not.toBeInTheDocument();
    });
  });
});