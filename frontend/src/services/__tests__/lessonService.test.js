import LessonService from '../lessonService';

// Mock axios
jest.mock('axios', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
}));

import axios from 'axios';

describe('LessonService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('listLessons', () => {
    test('successfully lists lessons', async () => {
      const mockResponse = {
        data: {
          success: true,
          lessons: [
            {
              lesson_number: 1,
              title: 'Introduction to Python',
              estimated_time: '30 minutes',
              difficulty: 'beginner'
            }
          ],
          summary: {
            user_id: 'user123',
            subject: 'python',
            total_lessons: 1
          }
        }
      };

      axios.get.mockResolvedValue(mockResponse);

      const result = await LessonService.listLessons('user123', 'python');

      expect(axios.get).toHaveBeenCalledWith(
        'http://localhost:5000/api/users/user123/subjects/python/lessons'
      );
      expect(result).toEqual(mockResponse.data);
    });

    test('handles API error', async () => {
      const mockError = {
        response: {
          status: 404,
          data: {
            success: false,
            error: 'not_found',
            message: 'Lessons not found'
          }
        }
      };

      axios.get.mockRejectedValue(mockError);

      await expect(LessonService.listLessons('user123', 'python'))
        .rejects
        .toThrow('Lessons not found');
    });

    test('handles network error', async () => {
      const mockError = {
        request: {}
      };

      axios.get.mockRejectedValue(mockError);

      await expect(LessonService.listLessons('user123', 'python'))
        .rejects
        .toThrow('Network error - please check your connection');
    });
  });

  describe('getLesson', () => {
    test('successfully gets a lesson', async () => {
      const mockResponse = {
        data: {
          success: true,
          lesson: {
            lesson_number: 1,
            title: 'Introduction to Python',
            estimated_time: '30 minutes',
            difficulty: 'beginner',
            topics: ['variables', 'data types'],
            content: '# Introduction\n\nThis is Python basics.'
          }
        }
      };

      axios.get.mockResolvedValue(mockResponse);

      const result = await LessonService.getLesson('user123', 'python', 1);

      expect(axios.get).toHaveBeenCalledWith(
        'http://localhost:5000/api/users/user123/subjects/python/lessons/1'
      );
      expect(result).toEqual(mockResponse.data);
    });

    test('handles lesson not found', async () => {
      const mockError = {
        response: {
          status: 404,
          data: {
            success: false,
            error: 'not_found',
            message: 'Lesson 5 not found for python'
          }
        }
      };

      axios.get.mockRejectedValue(mockError);

      await expect(LessonService.getLesson('user123', 'python', 5))
        .rejects
        .toThrow('Lesson 5 not found for python');
    });

    test('handles subscription required error', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {
            success: false,
            error: 'subscription_required',
            message: 'Active subscription required for python'
          }
        }
      };

      axios.get.mockRejectedValue(mockError);

      const error = await LessonService.getLesson('user123', 'python', 1)
        .catch(err => err);

      expect(error.message).toBe('Active subscription required for python');
      expect(error.type).toBe('subscription_required');
      expect(error.status).toBe(403);
    });
  });

  describe('getLessonProgress', () => {
    test('successfully gets lesson progress', async () => {
      const mockResponse = {
        data: {
          success: true,
          progress: {
            user_id: 'user123',
            subject: 'python',
            total_lessons_generated: 5,
            available_lessons: 3,
            progress_percentage: 60.0,
            skill_level: 'intermediate'
          }
        }
      };

      axios.get.mockResolvedValue(mockResponse);

      const result = await LessonService.getLessonProgress('user123', 'python');

      expect(axios.get).toHaveBeenCalledWith(
        'http://localhost:5000/api/users/user123/subjects/python/lessons/progress'
      );
      expect(result).toEqual(mockResponse.data);
    });

    test('handles progress retrieval error', async () => {
      const mockError = {
        response: {
          status: 500,
          data: {
            success: false,
            error: 'retrieval_error',
            message: 'Failed to retrieve lesson progress'
          }
        }
      };

      axios.get.mockRejectedValue(mockError);

      await expect(LessonService.getLessonProgress('user123', 'python'))
        .rejects
        .toThrow('Failed to retrieve lesson progress');
    });
  });

  describe('generateLessons', () => {
    test('successfully generates lessons', async () => {
      const mockResponse = {
        data: {
          success: true,
          generation_summary: {
            user_id: 'user123',
            subject: 'python',
            skill_level: 'beginner',
            total_lessons: 10,
            generated_at: '2024-01-15T10:00:00Z'
          },
          message: 'Successfully generated 10 personalized lessons for python'
        }
      };

      axios.post.mockResolvedValue(mockResponse);

      const result = await LessonService.generateLessons('user123', 'python');

      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:5000/api/users/user123/subjects/python/lessons/generate'
      );
      expect(result).toEqual(mockResponse.data);
    });

    test('handles generation error when survey not completed', async () => {
      const mockError = {
        response: {
          status: 404,
          data: {
            success: false,
            error: 'prerequisite_missing',
            message: 'Survey results not found. Please complete the subject survey first.',
            details: {
              required_action: 'complete_survey',
              subject: 'python'
            }
          }
        }
      };

      axios.post.mockRejectedValue(mockError);

      const error = await LessonService.generateLessons('user123', 'python')
        .catch(err => err);

      expect(error.message).toBe('Survey results not found. Please complete the subject survey first.');
      expect(error.type).toBe('prerequisite_missing');
      expect(error.details.required_action).toBe('complete_survey');
    });

    test('handles subscription required for generation', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {
            success: false,
            error: 'subscription_required',
            message: 'Active subscription required for python'
          }
        }
      };

      axios.post.mockRejectedValue(mockError);

      await expect(LessonService.generateLessons('user123', 'python'))
        .rejects
        .toThrow('Active subscription required for python');
    });
  });

  describe('handleError', () => {
    test('handles response error with details', () => {
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

      const error = LessonService.handleError(axiosError);

      expect(error.message).toBe('Invalid input');
      expect(error.type).toBe('validation_error');
      expect(error.status).toBe(400);
      expect(error.details).toEqual({ field: 'user_id' });
    });

    test('handles response error without message', () => {
      const axiosError = {
        response: {
          status: 500,
          data: {}
        }
      };

      const error = LessonService.handleError(axiosError);

      expect(error.message).toBe('An error occurred');
      expect(error.type).toBe('unknown_error');
      expect(error.status).toBe(500);
    });

    test('handles network error', () => {
      const axiosError = {
        request: {}
      };

      const error = LessonService.handleError(axiosError);

      expect(error.message).toBe('Network error - please check your connection');
      expect(error.type).toBe('network_error');
    });

    test('handles other errors', () => {
      const genericError = new Error('Something went wrong');

      const error = LessonService.handleError(genericError);

      expect(error).toBe(genericError);
    });
  });

  describe('markLessonCompleted', () => {
    test('successfully marks lesson as completed', async () => {
      const mockResponse = {
        data: {
          success: true,
          message: 'Lesson marked as completed',
          completion: {
            user_id: 'user123',
            subject: 'python',
            lesson_number: 1,
            completed_at: '2024-01-15T10:00:00Z'
          }
        }
      };

      axios.post.mockResolvedValue(mockResponse);

      const result = await LessonService.markLessonCompleted('user123', 'python', 1);

      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:5000/api/users/user123/subjects/python/lessons/1/complete'
      );
      expect(result).toEqual(mockResponse.data);
    });

    test('handles completion error', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            success: false,
            error: 'validation_error',
            message: 'Lesson already completed'
          }
        }
      };

      axios.post.mockRejectedValue(mockError);

      await expect(LessonService.markLessonCompleted('user123', 'python', 1))
        .rejects
        .toThrow('Lesson already completed');
    });
  });

  describe('getLessonCompletionStatus', () => {
    test('successfully gets completion status', async () => {
      const mockResponse = {
        data: {
          success: true,
          completed_lessons: [1, 2, 3],
          completion_summary: {
            user_id: 'user123',
            subject: 'python',
            total_completed: 3,
            completion_percentage: 30.0
          }
        }
      };

      axios.get.mockResolvedValue(mockResponse);

      const result = await LessonService.getLessonCompletionStatus('user123', 'python');

      expect(axios.get).toHaveBeenCalledWith(
        'http://localhost:5000/api/users/user123/subjects/python/lessons/completion'
      );
      expect(result).toEqual(mockResponse.data);
    });

    test('handles completion status retrieval error', async () => {
      const mockError = {
        response: {
          status: 404,
          data: {
            success: false,
            error: 'not_found',
            message: 'No completion data found'
          }
        }
      };

      axios.get.mockRejectedValue(mockError);

      await expect(LessonService.getLessonCompletionStatus('user123', 'python'))
        .rejects
        .toThrow('No completion data found');
    });
  });

  describe('API base URL configuration', () => {
    test('uses environment variable for API base URL', () => {
      const originalEnv = process.env.REACT_APP_API_BASE_URL;
      process.env.REACT_APP_API_BASE_URL = 'https://api.example.com';

      // Re-import to get updated environment variable
      jest.resetModules();
      const LessonServiceWithCustomURL = require('../lessonService').default;

      // Mock axios for this test
      axios.get.mockResolvedValue({ data: { success: true } });

      LessonServiceWithCustomURL.listLessons('user123', 'python');

      expect(axios.get).toHaveBeenCalledWith(
        'https://api.example.com/users/user123/subjects/python/lessons'
      );

      // Restore original environment
      process.env.REACT_APP_API_BASE_URL = originalEnv;
    });

    test('uses default URL when environment variable not set', () => {
      const originalEnv = process.env.REACT_APP_API_BASE_URL;
      delete process.env.REACT_APP_API_BASE_URL;

      // Re-import to get updated environment variable
      jest.resetModules();
      const LessonServiceWithDefaultURL = require('../lessonService').default;

      // Mock axios for this test
      axios.get.mockResolvedValue({ data: { success: true } });

      LessonServiceWithDefaultURL.listLessons('user123', 'python');

      expect(axios.get).toHaveBeenCalledWith(
        'http://localhost:5000/api/users/user123/subjects/python/lessons'
      );

      // Restore original environment
      process.env.REACT_APP_API_BASE_URL = originalEnv;
    });
  });
});