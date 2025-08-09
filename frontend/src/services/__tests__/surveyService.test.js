import SurveyService from '../surveyService';

// Mock fetch globally
global.fetch = jest.fn();

describe('SurveyService', () => {
  const mockUserId = 'test-user-123';
  const mockSubject = 'python';
  const mockApiUrl = 'http://localhost:5000/api';

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.REACT_APP_API_URL = mockApiUrl;
  });

  afterEach(() => {
    delete process.env.REACT_APP_API_URL;
  });

  const mockSurveyData = {
    id: 'survey-123',
    subject: 'python',
    subject_name: 'Python Programming',
    user_id: 'test-user-123',
    questions: [
      {
        id: 1,
        question: 'What is a list in Python?',
        type: 'multiple_choice',
        options: ['Array', 'Collection', 'Both', 'Neither'],
        difficulty: 'beginner',
        topic: 'data_structures'
      }
    ],
    metadata: {
      topics_covered: ['data_structures']
    }
  };

  const mockSurveyResults = {
    user_id: 'test-user-123',
    subject: 'python',
    skill_level: 'intermediate',
    accuracy: 75,
    total_questions: 1,
    correct_answers: 1,
    topic_analysis: {},
    recommendations: [],
    processed_at: '2024-01-15T10:30:00Z'
  };

  describe('generateSurvey', () => {
    test('generates survey successfully', async () => {
      const mockResponse = {
        success: true,
        survey: mockSurveyData
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SurveyService.generateSurvey(mockUserId, mockSubject);

      expect(fetch).toHaveBeenCalledWith(
        `${mockApiUrl}/users/${mockUserId}/subjects/${mockSubject}/survey/generate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      expect(result).toEqual(mockSurveyData);
    });

    test('handles API error response', async () => {
      const mockErrorResponse = {
        success: false,
        message: 'Failed to generate survey'
      };

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => mockErrorResponse
      });

      await expect(
        SurveyService.generateSurvey(mockUserId, mockSubject)
      ).rejects.toThrow('Failed to generate survey');
    });

    test('handles network error', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(
        SurveyService.generateSurvey(mockUserId, mockSubject)
      ).rejects.toThrow('Network error');
    });

    test('handles unsuccessful response', async () => {
      const mockResponse = {
        success: false,
        message: 'Validation failed'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      await expect(
        SurveyService.generateSurvey(mockUserId, mockSubject)
      ).rejects.toThrow('Validation failed');
    });
  });

  describe('getSurvey', () => {
    test('retrieves survey successfully', async () => {
      const mockResponse = {
        success: true,
        survey: mockSurveyData
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SurveyService.getSurvey(mockUserId, mockSubject);

      expect(fetch).toHaveBeenCalledWith(
        `${mockApiUrl}/users/${mockUserId}/subjects/${mockSubject}/survey`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      expect(result).toEqual(mockSurveyData);
    });

    test('handles 404 not found', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ message: 'Not found' })
      });

      await expect(
        SurveyService.getSurvey(mockUserId, mockSubject)
      ).rejects.toThrow('Survey not found. Please generate a survey first.');
    });

    test('handles other HTTP errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ message: 'Server error' })
      });

      await expect(
        SurveyService.getSurvey(mockUserId, mockSubject)
      ).rejects.toThrow('Server error');
    });
  });

  describe('submitSurvey', () => {
    const mockSubmissionData = {
      survey_id: 'survey-123',
      user_id: 'test-user-123',
      subject: 'python',
      answers: [
        {
          question_id: 1,
          answer: 0,
          question_text: 'What is a list in Python?',
          question_type: 'multiple_choice'
        }
      ]
    };

    test('submits survey successfully', async () => {
      const mockResponse = {
        success: true,
        results: mockSurveyResults
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SurveyService.submitSurvey(
        mockUserId,
        mockSubject,
        mockSubmissionData
      );

      expect(fetch).toHaveBeenCalledWith(
        `${mockApiUrl}/users/${mockUserId}/subjects/${mockSubject}/survey/submit`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(mockSubmissionData),
        }
      );

      expect(result).toEqual(mockSurveyResults);
    });

    test('handles submission error', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ message: 'Invalid submission' })
      });

      await expect(
        SurveyService.submitSurvey(mockUserId, mockSubject, mockSubmissionData)
      ).rejects.toThrow('Invalid submission');
    });

    test('handles survey not found during submission', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ message: 'Survey not found' })
      });

      await expect(
        SurveyService.submitSurvey(mockUserId, mockSubject, mockSubmissionData)
      ).rejects.toThrow('Survey not found. Please generate a survey first.');
    });
  });

  describe('getSurveyResults', () => {
    test('retrieves survey results successfully', async () => {
      const mockResponse = {
        success: true,
        results: mockSurveyResults
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SurveyService.getSurveyResults(mockUserId, mockSubject);

      expect(fetch).toHaveBeenCalledWith(
        `${mockApiUrl}/users/${mockUserId}/subjects/${mockSubject}/survey/results`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      expect(result).toEqual(mockSurveyResults);
    });

    test('handles results not found', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ message: 'Results not found' })
      });

      await expect(
        SurveyService.getSurveyResults(mockUserId, mockSubject)
      ).rejects.toThrow('Survey results not found.');
    });
  });

  describe('surveyExists', () => {
    test('returns true when survey exists', async () => {
      const mockResponse = {
        success: true,
        survey: mockSurveyData
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SurveyService.surveyExists(mockUserId, mockSubject);

      expect(result).toBe(true);
    });

    test('returns false when survey does not exist', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ message: 'Survey not found' })
      });

      const result = await SurveyService.surveyExists(mockUserId, mockSubject);

      expect(result).toBe(false);
    });

    test('throws error for other failures', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ message: 'Server error' })
      });

      await expect(
        SurveyService.surveyExists(mockUserId, mockSubject)
      ).rejects.toThrow('Server error');
    });
  });

  describe('getOrGenerateSurvey', () => {
    test('returns existing survey when available', async () => {
      const mockResponse = {
        success: true,
        survey: mockSurveyData
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SurveyService.getOrGenerateSurvey(mockUserId, mockSubject);

      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetch).toHaveBeenCalledWith(
        `${mockApiUrl}/users/${mockUserId}/subjects/${mockSubject}/survey`,
        expect.any(Object)
      );
      expect(result).toEqual(mockSurveyData);
    });

    test('generates new survey when existing not found', async () => {
      // First call (getSurvey) fails with 404
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ message: 'Survey not found' })
      });

      // Second call (generateSurvey) succeeds
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, survey: mockSurveyData })
      });

      const result = await SurveyService.getOrGenerateSurvey(mockUserId, mockSubject);

      expect(fetch).toHaveBeenCalledTimes(2);
      expect(result).toEqual(mockSurveyData);
    });

    test('forces generation when requested', async () => {
      const mockResponse = {
        success: true,
        survey: mockSurveyData
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SurveyService.getOrGenerateSurvey(
        mockUserId,
        mockSubject,
        true // forceGenerate
      );

      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetch).toHaveBeenCalledWith(
        `${mockApiUrl}/users/${mockUserId}/subjects/${mockSubject}/survey/generate`,
        expect.any(Object)
      );
      expect(result).toEqual(mockSurveyData);
    });
  });

  describe('validateSurveyData', () => {
    test('validates correct survey data', () => {
      const validSurvey = {
        subject: 'python',
        user_id: 'test-user',
        questions: [
          {
            id: 1,
            question: 'Test question?',
            type: 'multiple_choice',
            options: ['A', 'B', 'C', 'D']
          }
        ]
      };

      expect(SurveyService.validateSurveyData(validSurvey)).toBe(true);
    });

    test('rejects invalid survey data', () => {
      // Missing required fields
      expect(SurveyService.validateSurveyData({})).toBe(false);
      expect(SurveyService.validateSurveyData(null)).toBe(false);
      expect(SurveyService.validateSurveyData('invalid')).toBe(false);

      // Missing questions
      expect(SurveyService.validateSurveyData({
        subject: 'python',
        user_id: 'test-user'
      })).toBe(false);

      // Invalid questions array
      expect(SurveyService.validateSurveyData({
        subject: 'python',
        user_id: 'test-user',
        questions: 'not-array'
      })).toBe(false);

      // Invalid question structure
      expect(SurveyService.validateSurveyData({
        subject: 'python',
        user_id: 'test-user',
        questions: [{ invalid: 'question' }]
      })).toBe(false);

      // Multiple choice without options
      expect(SurveyService.validateSurveyData({
        subject: 'python',
        user_id: 'test-user',
        questions: [{
          id: 1,
          question: 'Test?',
          type: 'multiple_choice'
        }]
      })).toBe(false);
    });
  });

  describe('formatSubmissionData', () => {
    test('formats submission data correctly', () => {
      const surveyData = {
        id: 'survey-123',
        user_id: 'test-user',
        subject: 'python',
        questions: [
          {
            id: 1,
            question: 'Test question?',
            type: 'multiple_choice',
            difficulty: 'beginner',
            topic: 'basics'
          }
        ]
      };

      const answers = { 1: 0 };

      const result = SurveyService.formatSubmissionData(surveyData, answers);

      expect(result).toEqual({
        survey_id: 'survey-123',
        user_id: 'test-user',
        subject: 'python',
        answers: [
          {
            question_id: 1,
            answer: 0,
            question_text: 'Test question?',
            question_type: 'multiple_choice',
            difficulty: 'beginner',
            topic: 'basics'
          }
        ],
        completed_at: expect.any(String)
      });

      // Check that completed_at is a valid ISO string
      expect(new Date(result.completed_at)).toBeInstanceOf(Date);
    });
  });

  describe('API URL configuration', () => {
    test('uses environment variable for API URL', async () => {
      const originalEnv = process.env.REACT_APP_API_URL;
      process.env.REACT_APP_API_URL = 'https://custom-api.com/api';

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, survey: mockSurveyData })
      });

      // Need to re-import the service to pick up the new environment variable
      jest.resetModules();
      const { default: TestSurveyService } = await import('../surveyService');
      
      await TestSurveyService.generateSurvey(mockUserId, mockSubject);

      expect(fetch).toHaveBeenCalledWith(
        `https://custom-api.com/api/users/${mockUserId}/subjects/${mockSubject}/survey/generate`,
        expect.any(Object)
      );

      // Restore original environment
      process.env.REACT_APP_API_URL = originalEnv;
    });

    test('uses default API URL when environment variable not set', async () => {
      delete process.env.REACT_APP_API_URL;

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, survey: mockSurveyData })
      });

      await SurveyService.generateSurvey(mockUserId, mockSubject);

      expect(fetch).toHaveBeenCalledWith(
        `http://localhost:5000/api/users/${mockUserId}/subjects/${mockSubject}/survey/generate`,
        expect.any(Object)
      );
    });
  });
});