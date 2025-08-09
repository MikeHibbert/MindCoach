import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Survey from '../Survey';

// Mock survey data
const mockSurveyData = {
  id: 'survey-123',
  subject: 'python',
  subject_name: 'Python Programming',
  user_id: 'user-456',
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
  }
};

describe('Survey Component', () => {
  const mockOnSubmit = jest.fn();
  const mockOnProgress = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading and Error States', () => {
    test('displays loading state', () => {
      render(
        <Survey
          surveyData={null}
          onSubmit={mockOnSubmit}
          isLoading={true}
        />
      );

      expect(screen.getByText('Loading survey...')).toBeInTheDocument();
      expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument();
    });

    test('displays error state', () => {
      const errorMessage = 'Failed to load survey';
      render(
        <Survey
          surveyData={null}
          onSubmit={mockOnSubmit}
          error={errorMessage}
        />
      );

      expect(screen.getByText('⚠️ Error Loading Survey')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
    });

    test('displays no survey available state', () => {
      render(
        <Survey
          surveyData={{ questions: [] }}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByText('📝 No Survey Available')).toBeInTheDocument();
      expect(screen.getByText('Please generate a survey first.')).toBeInTheDocument();
    });
  });

  describe('Survey Rendering', () => {
    test('renders survey header with correct information', () => {
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
          onProgress={mockOnProgress}
        />
      );

      expect(screen.getByText('Python Programming Assessment')).toBeInTheDocument();
      expect(screen.getByText('Question 1 of 3')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    test('renders first question correctly', () => {
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByText('What is the correct way to create a list in Python?')).toBeInTheDocument();
      expect(screen.getByText('beginner')).toBeInTheDocument();
      expect(screen.getByText('Topic: data structures')).toBeInTheDocument();
    });

    test('renders multiple choice options', () => {
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByLabelText('list = []')).toBeInTheDocument();
      expect(screen.getByLabelText('list = {}')).toBeInTheDocument();
      expect(screen.getByLabelText('list = ()')).toBeInTheDocument();
      expect(screen.getByLabelText('list = ""')).toBeInTheDocument();
    });

    test('renders survey info at bottom', () => {
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByText(/This assessment helps us understand/)).toBeInTheDocument();
      expect(screen.getByText(/Topics covered: data structures, concepts/)).toBeInTheDocument();
    });
  });

  describe('Question Types', () => {
    test('renders multiple choice question correctly', () => {
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      const radioButtons = screen.getAllByRole('radio');
      expect(radioButtons).toHaveLength(4);
      
      // Check that all options are rendered
      mockSurveyData.questions[0].options.forEach(option => {
        expect(screen.getByLabelText(option)).toBeInTheDocument();
      });
    });

    test('renders true/false question correctly', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Navigate to second question (true/false)
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));

      expect(screen.getByText('Python supports object-oriented programming.')).toBeInTheDocument();
      expect(screen.getByLabelText('True')).toBeInTheDocument();
      expect(screen.getByLabelText('False')).toBeInTheDocument();
    });

    test('renders text question correctly', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Navigate to third question (text)
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.click(screen.getByLabelText('True'));
      await user.click(screen.getByRole('button', { name: /Next/ }));

      expect(screen.getByText('Explain the difference between a list and a tuple.')).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your answer here...')).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    test('previous button is disabled on first question', () => {
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      const previousButton = screen.getByRole('button', { name: /Previous/ });
      expect(previousButton).toBeDisabled();
    });

    test('can navigate to next question after answering', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Answer first question
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      
      // Navigate to next question
      await user.click(screen.getByRole('button', { name: /Next/ }));

      expect(screen.getByText('Question 2 of 3')).toBeInTheDocument();
      expect(screen.getByText('Python supports object-oriented programming.')).toBeInTheDocument();
    });

    test('can navigate back to previous question', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Answer first question and go to second
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));

      // Go back to first question
      await user.click(screen.getByRole('button', { name: /Previous/ }));

      expect(screen.getByText('Question 1 of 3')).toBeInTheDocument();
      expect(screen.getByText('What is the correct way to create a list in Python?')).toBeInTheDocument();
    });

    test('shows submit button on last question', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Navigate to last question
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.click(screen.getByLabelText('True'));
      await user.click(screen.getByRole('button', { name: /Next/ }));

      expect(screen.getByRole('button', { name: /Submit Survey/ })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Next/ })).not.toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    test('shows validation error when trying to proceed without answering', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Try to go to next question without answering
      await user.click(screen.getByRole('button', { name: /Next/ }));

      expect(screen.getByText('Please select an answer before continuing.')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    test('clears validation error when answer is provided', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Try to proceed without answering
      await user.click(screen.getByRole('button', { name: /Next/ }));
      expect(screen.getByText('Please select an answer before continuing.')).toBeInTheDocument();

      // Provide answer
      await user.click(screen.getByRole('radio', { name: 'list = []' }));

      // Error should be cleared
      expect(screen.queryByText('Please select an answer before continuing.')).not.toBeInTheDocument();
    });

    test('validates all questions before submission', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Navigate to last question without answering all
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.click(screen.getByRole('button', { name: /Next/ })); // Skip second question
      const textArea = screen.getByRole('textbox');
      await user.type(textArea, 'Some answer');

      // Try to submit
      await user.click(screen.getByRole('button', { name: /Submit Survey/ }));

      // Should not call onSubmit and should show validation errors
      expect(mockOnSubmit).not.toHaveBeenCalled();
      
      // Should navigate back to first unanswered question
      await waitFor(() => {
        expect(screen.getByText('Question 2 of 3')).toBeInTheDocument();
      });
    });
  });

  describe('Answer Selection', () => {
    test('selects and deselects multiple choice answers', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      const firstOption = screen.getByRole('radio', { name: 'list = []' });
      const secondOption = screen.getByRole('radio', { name: 'list = {}' });

      // Select first option
      await user.click(firstOption);
      expect(firstOption).toBeChecked();

      // Select second option (should deselect first)
      await user.click(secondOption);
      expect(secondOption).toBeChecked();
      expect(firstOption).not.toBeChecked();
    });

    test('handles text input answers', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Navigate to text question
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.click(screen.getByLabelText('True'));
      await user.click(screen.getByRole('button', { name: /Next/ }));

      const textArea = screen.getByRole('textbox');
      const testAnswer = 'Lists are mutable, tuples are immutable.';
      
      await user.type(textArea, testAnswer);
      expect(textArea).toHaveValue(testAnswer);
    });

    test('preserves answers when navigating between questions', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Answer first question
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));

      // Answer second question
      await user.click(screen.getByLabelText('True'));
      await user.click(screen.getByRole('button', { name: /Previous/ }));

      // Check that first answer is preserved
      expect(screen.getByRole('radio', { name: 'list = []' })).toBeChecked();
    });
  });

  describe('Progress Tracking', () => {
    test('calls onProgress with correct data', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
          onProgress={mockOnProgress}
        />
      );

      // Initial progress
      expect(mockOnProgress).toHaveBeenCalledWith({
        currentQuestion: 1,
        totalQuestions: 3,
        answeredQuestions: 0,
        progressPercentage: 0
      });

      // Answer first question
      await user.click(screen.getByRole('radio', { name: 'list = []' }));

      expect(mockOnProgress).toHaveBeenCalledWith({
        currentQuestion: 1,
        totalQuestions: 3,
        answeredQuestions: 1,
        progressPercentage: 33
      });
    });

    test('updates progress bar correctly', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      
      // Initial progress (33% for being on question 1 of 3)
      expect(progressBar).toHaveAttribute('aria-valuenow', '33');

      // Navigate to second question
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));

      expect(progressBar).toHaveAttribute('aria-valuenow', '67');
    });
  });

  describe('Survey Submission', () => {
    test('submits survey with correct data format', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue();

      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Answer all questions
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      
      await user.click(screen.getByLabelText('True'));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      
      await user.type(screen.getByRole('textbox'), 'Lists are mutable, tuples are immutable.');

      // Submit survey
      await user.click(screen.getByRole('button', { name: /Submit Survey/ }));

      expect(mockOnSubmit).toHaveBeenCalledWith({
        survey_id: 'survey-123',
        user_id: 'user-456',
        subject: 'python',
        answers: [
          {
            question_id: 1,
            answer: 0,
            question_text: 'What is the correct way to create a list in Python?',
            question_type: 'multiple_choice',
            difficulty: 'beginner',
            topic: 'data_structures'
          },
          {
            question_id: 2,
            answer: 0,
            question_text: 'Python supports object-oriented programming.',
            question_type: 'true_false',
            difficulty: 'beginner',
            topic: 'concepts'
          },
          {
            question_id: 3,
            answer: 'Lists are mutable, tuples are immutable.',
            question_text: 'Explain the difference between a list and a tuple.',
            question_type: 'text',
            difficulty: 'intermediate',
            topic: 'data_structures'
          }
        ],
        completed_at: expect.any(String)
      });
    });

    test('shows loading state during submission', async () => {
      const user = userEvent.setup();
      let resolveSubmit;
      const submitPromise = new Promise(resolve => {
        resolveSubmit = resolve;
      });
      mockOnSubmit.mockReturnValue(submitPromise);

      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Answer all questions quickly
      await user.click(screen.getByRole('radio', { name: 'list = []' }));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.click(screen.getByLabelText('True'));
      await user.click(screen.getByRole('button', { name: /Next/ }));
      await user.type(screen.getByRole('textbox'), 'Test answer');

      // Submit survey
      await user.click(screen.getByRole('button', { name: /Submit Survey/ }));

      // Check loading state
      expect(screen.getByText('Submitting...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Submitting.../ })).toBeDisabled();

      // Resolve submission
      resolveSubmit();
      await waitFor(() => {
        expect(screen.queryByText('Submitting...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', () => {
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-label', 'Survey progress: 33% complete');
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '33');
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuemin', '0');
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuemax', '100');
    });

    test('associates error messages with form controls', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Trigger validation error
      await user.click(screen.getByRole('button', { name: /Next/ }));

      const errorMessage = screen.getByRole('alert');
      const radioButtons = screen.getAllByRole('radio');
      
      expect(errorMessage).toHaveAttribute('id', 'error-1');
      radioButtons.forEach(radio => {
        expect(radio).toHaveAttribute('aria-describedby', 'error-1');
      });
    });

    test('has proper focus management', async () => {
      const user = userEvent.setup();
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Tab through radio buttons
      await user.tab();
      expect(screen.getAllByRole('radio')[0]).toHaveFocus();

      await user.tab();
      expect(screen.getAllByRole('radio')[1]).toHaveFocus();
    });
  });

  describe('Responsive Design', () => {
    test('applies mobile-specific classes', () => {
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Check for mobile-specific classes
      const options = screen.getAllByRole('radio').map(radio => radio.closest('label'));
      options.forEach(option => {
        expect(option).toHaveClass('mobile:min-h-[56px]');
      });
    });

    test('applies tablet-specific classes', () => {
      render(
        <Survey
          surveyData={mockSurveyData}
          onSubmit={mockOnSubmit}
        />
      );

      // Check for tablet-specific classes
      const options = screen.getAllByRole('radio').map(radio => radio.closest('label'));
      options.forEach(option => {
        expect(option).toHaveClass('tablet:min-h-[60px]');
      });
    });
  });
});