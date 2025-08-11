import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PipelineProgressTracker from '../PipelineProgressTracker';
import PipelineService from '../../services/pipelineService';

// Mock the PipelineService
jest.mock('../../services/pipelineService');

// Mock accessibility utils
jest.mock('../../utils/accessibility', () => ({
  announceToScreenReader: jest.fn(),
  focusManagement: {
    setFocus: jest.fn()
  }
}));

describe('PipelineProgressTracker', () => {
  const mockProps = {
    userId: 'test-user-123',
    subject: 'python',
    onComplete: jest.fn(),
    onError: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial State', () => {
    test('renders start button when not started', () => {
      render(<PipelineProgressTracker {...mockProps} />);
      
      expect(screen.getByText('Ready to Generate Your Learning Content')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /start content generation pipeline/i })).toBeInTheDocument();
    });

    test('shows message when userId or subject is missing', () => {
      render(<PipelineProgressTracker userId="" subject="python" />);
      
      expect(screen.getByText('Please select a subject to generate content.')).toBeInTheDocument();
    });
  });

  describe('Pipeline Start', () => {
    test('starts pipeline when start button is clicked', async () => {
      const mockResponse = {
        success: true,
        pipeline_id: 'pipeline-123',
        message: 'Pipeline started'
      };
      
      PipelineService.startContentGeneration.mockResolvedValue(mockResponse);
      PipelineService.pollPipelineStatus.mockImplementation((userId, subject, pipelineId, onUpdate, onComplete) => {
        // Simulate immediate completion for test
        setTimeout(() => onComplete({ status: 'completed', progress_percentage: 100 }), 100);
      });

      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      fireEvent.click(startButton);

      expect(PipelineService.startContentGeneration).toHaveBeenCalledWith('test-user-123', 'python');
      
      // Should show starting state
      await waitFor(() => {
        expect(screen.getByText('Starting Pipeline...')).toBeInTheDocument();
      });
    });

    test('handles pipeline start error', async () => {
      const mockError = new Error('Failed to start pipeline');
      PipelineService.startContentGeneration.mockRejectedValue(mockError);

      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText('Content Generation Failed')).toBeInTheDocument();
        expect(screen.getByText('Failed to start pipeline')).toBeInTheDocument();
      });

      expect(mockProps.onError).toHaveBeenCalledWith(mockError);
    });
  });

  describe('Progress Display', () => {
    test('displays progress during pipeline execution', async () => {
      const mockResponse = {
        success: true,
        pipeline_id: 'pipeline-123'
      };
      
      PipelineService.startContentGeneration.mockResolvedValue(mockResponse);
      PipelineService.pollPipelineStatus.mockImplementation((userId, subject, pipelineId, onUpdate) => {
        // Simulate progress updates
        setTimeout(() => onUpdate({
          status: 'in_progress',
          current_stage: 'curriculum_generation',
          progress_percentage: 20,
          message: 'Generating curriculum'
        }), 100);
      });

      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText('Generating Learning Content')).toBeInTheDocument();
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Curriculum Generation')).toBeInTheDocument();
        expect(screen.getByText('20%')).toBeInTheDocument();
      });
    });

    test('shows lesson generation progress', async () => {
      const mockResponse = {
        success: true,
        pipeline_id: 'pipeline-123'
      };
      
      PipelineService.startContentGeneration.mockResolvedValue(mockResponse);
      PipelineService.pollPipelineStatus.mockImplementation((userId, subject, pipelineId, onUpdate) => {
        setTimeout(() => onUpdate({
          status: 'in_progress',
          current_stage: 'content_generation',
          progress_percentage: 80,
          lessons_completed: 3,
          total_lessons: 10,
          message: 'Generating lesson content'
        }), 100);
      });

      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText('Lessons Generated')).toBeInTheDocument();
        expect(screen.getByText('3 / 10')).toBeInTheDocument();
      });
    });
  });

  describe('Pipeline Completion', () => {
    test('handles successful completion', async () => {
      const mockResponse = {
        success: true,
        pipeline_id: 'pipeline-123'
      };
      
      const completionStatus = {
        status: 'completed',
        progress_percentage: 100,
        message: 'All lessons generated successfully'
      };
      
      PipelineService.startContentGeneration.mockResolvedValue(mockResponse);
      PipelineService.pollPipelineStatus.mockImplementation((userId, subject, pipelineId, onUpdate, onComplete) => {
        setTimeout(() => onComplete(completionStatus), 100);
      });

      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(mockProps.onComplete).toHaveBeenCalledWith(completionStatus);
      });
    });
  });

  describe('Error Handling', () => {
    test('displays subscription required error', async () => {
      const subscriptionError = new Error('Active subscription required');
      subscriptionError.type = 'subscription_required';
      
      PipelineService.startContentGeneration.mockRejectedValue(subscriptionError);

      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText('Content Generation Failed')).toBeInTheDocument();
        expect(screen.getByText('You need an active subscription to generate content for this subject.')).toBeInTheDocument();
      });
    });

    test('displays prerequisite missing error', async () => {
      const prerequisiteError = new Error('Survey results not found');
      prerequisiteError.type = 'prerequisite_missing';
      
      PipelineService.startContentGeneration.mockRejectedValue(prerequisiteError);

      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText('Content Generation Failed')).toBeInTheDocument();
        expect(screen.getByText('Please complete the subject survey before generating lessons.')).toBeInTheDocument();
      });
    });

    test('allows retry on error', async () => {
      const mockError = new Error('Network error');
      PipelineService.startContentGeneration
        .mockRejectedValueOnce(mockError)
        .mockResolvedValueOnce({ success: true, pipeline_id: 'pipeline-123' });

      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText('Content Generation Failed')).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /retry content generation/i });
      fireEvent.click(retryButton);

      expect(PipelineService.startContentGeneration).toHaveBeenCalledTimes(2);
    });

    test('limits retry attempts', async () => {
      const mockError = new Error('Persistent error');
      PipelineService.startContentGeneration.mockRejectedValue(mockError);

      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      fireEvent.click(startButton);

      // Retry 3 times
      for (let i = 0; i < 3; i++) {
        await waitFor(() => {
          expect(screen.getByText('Content Generation Failed')).toBeInTheDocument();
        });

        const retryButton = screen.getByRole('button', { name: /retry content generation/i });
        fireEvent.click(retryButton);
      }

      await waitFor(() => {
        expect(screen.getByText('Maximum retry attempts reached. Please try again later or contact support.')).toBeInTheDocument();
      });

      expect(PipelineService.startContentGeneration).toHaveBeenCalledTimes(4); // Initial + 3 retries
    });
  });

  describe('Auto Start', () => {
    test('automatically starts pipeline when autoStart is true', async () => {
      const mockResponse = {
        success: true,
        pipeline_id: 'pipeline-123'
      };
      
      PipelineService.startContentGeneration.mockResolvedValue(mockResponse);
      PipelineService.pollPipelineStatus.mockImplementation(() => {});

      render(<PipelineProgressTracker {...mockProps} autoStart={true} />);

      await waitFor(() => {
        expect(PipelineService.startContentGeneration).toHaveBeenCalledWith('test-user-123', 'python');
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', () => {
      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      expect(startButton).toBeInTheDocument();
    });

    test('progress bar has proper accessibility attributes', async () => {
      const mockResponse = {
        success: true,
        pipeline_id: 'pipeline-123'
      };
      
      PipelineService.startContentGeneration.mockResolvedValue(mockResponse);
      PipelineService.pollPipelineStatus.mockImplementation((userId, subject, pipelineId, onUpdate) => {
        setTimeout(() => onUpdate({
          status: 'in_progress',
          current_stage: 'curriculum_generation',
          progress_percentage: 30
        }), 100);
      });

      render(<PipelineProgressTracker {...mockProps} />);
      
      const startButton = screen.getByRole('button', { name: /start content generation pipeline/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toHaveAttribute('aria-valuenow', '30');
        expect(progressBar).toHaveAttribute('aria-valuemin', '0');
        expect(progressBar).toHaveAttribute('aria-valuemax', '100');
      });
    });
  });
});