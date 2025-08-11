import axios from 'axios';
import PipelineService from '../pipelineService';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

describe('PipelineService', () => {
  const API_BASE_URL = 'http://localhost:5000/api';
  const userId = 'test-user-123';
  const subject = 'python';
  const pipelineId = 'pipeline-456';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('startContentGeneration', () => {
    test('successfully starts content generation', async () => {
      const mockResponse = {
        data: {
          success: true,
          pipeline_id: pipelineId,
          message: 'Pipeline started successfully'
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await PipelineService.startContentGeneration(userId, subject);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lessons/generate-langchain`
      );
      expect(result).toEqual(mockResponse.data);
    });

    test('handles API error', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            error: 'validation_error',
            message: 'Invalid user ID format'
          }
        }
      };

      mockedAxios.post.mockRejectedValue(mockError);

      await expect(PipelineService.startContentGeneration(userId, subject))
        .rejects.toThrow('Invalid user ID format');
    });

    test('handles network error', async () => {
      const mockError = {
        request: {}
      };

      mockedAxios.post.mockRejectedValue(mockError);

      await expect(PipelineService.startContentGeneration(userId, subject))
        .rejects.toThrow('Network error - please check your connection');
    });
  });

  describe('getPipelineStatus', () => {
    test('successfully gets pipeline status', async () => {
      const mockResponse = {
        data: {
          success: true,
          pipeline_status: {
            status: 'in_progress',
            current_stage: 'curriculum_generation',
            progress_percentage: 30
          }
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await PipelineService.getPipelineStatus(userId, subject, pipelineId);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lessons/pipeline-status/${pipelineId}`
      );
      expect(result).toEqual(mockResponse.data);
    });

    test('handles pipeline not found error', async () => {
      const mockError = {
        response: {
          status: 404,
          data: {
            error: 'not_found',
            message: 'Pipeline not found'
          }
        }
      };

      mockedAxios.get.mockRejectedValue(mockError);

      await expect(PipelineService.getPipelineStatus(userId, subject, pipelineId))
        .rejects.toThrow('Pipeline not found');
    });
  });

  describe('getCurriculumScheme', () => {
    test('successfully gets curriculum scheme', async () => {
      const mockResponse = {
        data: {
          success: true,
          curriculum: {
            subject: 'python',
            skill_level: 'intermediate',
            topics: ['variables', 'functions', 'classes']
          }
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await PipelineService.getCurriculumScheme(userId, subject);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/curriculum`
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getLessonPlans', () => {
    test('successfully gets lesson plans', async () => {
      const mockResponse = {
        data: {
          success: true,
          lesson_plans: {
            lesson_plans: [
              {
                lesson_id: 1,
                title: 'Python Basics',
                learning_objectives: ['Understand variables', 'Use basic operators']
              }
            ]
          }
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await PipelineService.getLessonPlans(userId, subject);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lesson-plans`
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('pollPipelineStatus', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    test('polls until completion', async () => {
      const onUpdate = jest.fn();
      const onComplete = jest.fn();
      const onError = jest.fn();

      const progressResponse = {
        data: {
          success: true,
          pipeline_status: {
            status: 'in_progress',
            current_stage: 'curriculum_generation',
            progress_percentage: 30
          }
        }
      };

      const completedResponse = {
        data: {
          success: true,
          pipeline_status: {
            status: 'completed',
            progress_percentage: 100
          }
        }
      };

      mockedAxios.get
        .mockResolvedValueOnce(progressResponse)
        .mockResolvedValueOnce(completedResponse);

      PipelineService.pollPipelineStatus(
        userId, 
        subject, 
        pipelineId, 
        onUpdate, 
        onComplete, 
        onError,
        1000
      );

      // First poll - in progress
      await Promise.resolve();
      expect(onUpdate).toHaveBeenCalledWith(progressResponse.data.pipeline_status);

      // Advance timer and second poll - completed
      jest.advanceTimersByTime(1000);
      await Promise.resolve();
      expect(onComplete).toHaveBeenCalledWith(completedResponse.data.pipeline_status);
    });

    test('handles polling error', async () => {
      const onUpdate = jest.fn();
      const onComplete = jest.fn();
      const onError = jest.fn();

      const mockError = new Error('Network error');
      mockedAxios.get.mockRejectedValue(mockError);

      PipelineService.pollPipelineStatus(
        userId, 
        subject, 
        pipelineId, 
        onUpdate, 
        onComplete, 
        onError
      );

      await Promise.resolve();
      expect(onError).toHaveBeenCalledWith(mockError);
    });

    test('handles failed pipeline status', async () => {
      const onUpdate = jest.fn();
      const onComplete = jest.fn();
      const onError = jest.fn();

      const failedResponse = {
        data: {
          success: true,
          pipeline_status: {
            status: 'failed',
            error_message: 'Pipeline execution failed'
          }
        }
      };

      mockedAxios.get.mockResolvedValue(failedResponse);

      PipelineService.pollPipelineStatus(
        userId, 
        subject, 
        pipelineId, 
        onUpdate, 
        onComplete, 
        onError
      );

      await Promise.resolve();
      expect(onError).toHaveBeenCalledWith(new Error('Pipeline execution failed'));
    });

    test('times out after maximum polls', async () => {
      const onUpdate = jest.fn();
      const onComplete = jest.fn();
      const onError = jest.fn();

      const progressResponse = {
        data: {
          success: true,
          pipeline_status: {
            status: 'in_progress',
            current_stage: 'curriculum_generation',
            progress_percentage: 30
          }
        }
      };

      mockedAxios.get.mockResolvedValue(progressResponse);

      PipelineService.pollPipelineStatus(
        userId, 
        subject, 
        pipelineId, 
        onUpdate, 
        onComplete, 
        onError,
        100 // Short interval for testing
      );

      // Simulate many polls to trigger timeout
      for (let i = 0; i < 301; i++) {
        jest.advanceTimersByTime(100);
        await Promise.resolve();
      }

      expect(onError).toHaveBeenCalledWith(
        new Error('Pipeline polling timeout - maximum polling time exceeded')
      );
    });
  });

  describe('handleError', () => {
    test('handles response error', () => {
      const axiosError = {
        response: {
          status: 400,
          data: {
            error: 'validation_error',
            message: 'Invalid input',
            details: { field: 'user_id' }
          }
        }
      };

      const result = PipelineService.handleError(axiosError);

      expect(result.message).toBe('Invalid input');
      expect(result.type).toBe('validation_error');
      expect(result.status).toBe(400);
      expect(result.details).toEqual({ field: 'user_id' });
    });

    test('handles request error', () => {
      const axiosError = {
        request: {}
      };

      const result = PipelineService.handleError(axiosError);

      expect(result.message).toBe('Network error - please check your connection');
      expect(result.type).toBe('network_error');
    });

    test('handles other errors', () => {
      const genericError = new Error('Something went wrong');

      const result = PipelineService.handleError(genericError);

      expect(result).toBe(genericError);
    });
  });
});