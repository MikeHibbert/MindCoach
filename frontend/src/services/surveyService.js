/**
 * Survey service for handling survey-related API calls
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

class SurveyService {
  /**
   * Generate a new survey for a user and subject
   * @param {string} userId - The user ID
   * @param {string} subject - The subject for the survey
   * @returns {Promise<Object>} The generated survey data
   */
  static async generateSurvey(userId, subject) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/survey/generate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }

      if (!data.success) {
        throw new Error(data.message || 'Failed to generate survey');
      }

      return data.survey;
    } catch (error) {
      console.error('Error generating survey:', error);
      throw new Error(
        error.message || 'Failed to generate survey. Please try again.'
      );
    }
  }

  /**
   * Retrieve an existing survey for a user and subject
   * @param {string} userId - The user ID
   * @param {string} subject - The subject for the survey
   * @returns {Promise<Object>} The survey data
   */
  static async getSurvey(userId, subject) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/survey`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Survey not found. Please generate a survey first.');
        }
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }

      if (!data.success) {
        throw new Error(data.message || 'Failed to retrieve survey');
      }

      return data.survey;
    } catch (error) {
      console.error('Error retrieving survey:', error);
      throw new Error(
        error.message || 'Failed to retrieve survey. Please try again.'
      );
    }
  }

  /**
   * Submit survey answers and get analysis results
   * @param {string} userId - The user ID
   * @param {string} subject - The subject for the survey
   * @param {Object} submissionData - The survey submission data
   * @returns {Promise<Object>} The analysis results
   */
  static async submitSurvey(userId, subject, submissionData) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/survey/submit`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submissionData),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Survey not found. Please generate a survey first.');
        }
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }

      if (!data.success) {
        throw new Error(data.message || 'Failed to submit survey');
      }

      return data.results;
    } catch (error) {
      console.error('Error submitting survey:', error);
      throw new Error(
        error.message || 'Failed to submit survey. Please try again.'
      );
    }
  }

  /**
   * Get survey analysis results for a user and subject
   * @param {string} userId - The user ID
   * @param {string} subject - The subject for the survey
   * @returns {Promise<Object>} The analysis results
   */
  static async getSurveyResults(userId, subject) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/survey/results`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Survey results not found.');
        }
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }

      if (!data.success) {
        throw new Error(data.message || 'Failed to retrieve survey results');
      }

      return data.results;
    } catch (error) {
      console.error('Error retrieving survey results:', error);
      throw new Error(
        error.message || 'Failed to retrieve survey results. Please try again.'
      );
    }
  }

  /**
   * Check if a survey exists for a user and subject
   * @param {string} userId - The user ID
   * @param {string} subject - The subject for the survey
   * @returns {Promise<boolean>} Whether the survey exists
   */
  static async surveyExists(userId, subject) {
    try {
      await this.getSurvey(userId, subject);
      return true;
    } catch (error) {
      if (error.message.includes('Survey not found')) {
        return false;
      }
      throw error;
    }
  }

  /**
   * Get or generate a survey for a user and subject
   * @param {string} userId - The user ID
   * @param {string} subject - The subject for the survey
   * @param {boolean} forceGenerate - Whether to force generation of a new survey
   * @returns {Promise<Object>} The survey data
   */
  static async getOrGenerateSurvey(userId, subject, forceGenerate = false) {
    try {
      if (!forceGenerate) {
        // Try to get existing survey first
        try {
          return await this.getSurvey(userId, subject);
        } catch (error) {
          if (!error.message.includes('Survey not found')) {
            throw error;
          }
          // Survey doesn't exist, generate a new one
        }
      }

      // Generate new survey
      return await this.generateSurvey(userId, subject);
    } catch (error) {
      console.error('Error getting or generating survey:', error);
      throw error;
    }
  }

  /**
   * Validate survey data structure
   * @param {Object} surveyData - The survey data to validate
   * @returns {boolean} Whether the survey data is valid
   */
  static validateSurveyData(surveyData) {
    if (!surveyData || typeof surveyData !== 'object') {
      return false;
    }

    const requiredFields = ['subject', 'user_id', 'questions'];
    for (const field of requiredFields) {
      if (!(field in surveyData)) {
        return false;
      }
    }

    if (!Array.isArray(surveyData.questions)) {
      return false;
    }

    // Validate each question
    for (const question of surveyData.questions) {
      const requiredQuestionFields = ['id', 'question', 'type'];
      for (const field of requiredQuestionFields) {
        if (!(field in question)) {
          return false;
        }
      }

      // Validate question type specific fields
      if (question.type === 'multiple_choice' && !Array.isArray(question.options)) {
        return false;
      }
    }

    return true;
  }

  /**
   * Format survey submission data
   * @param {Object} surveyData - The original survey data
   * @param {Object} answers - The user's answers
   * @returns {Object} Formatted submission data
   */
  static formatSubmissionData(surveyData, answers) {
    const formattedAnswers = surveyData.questions.map(question => ({
      question_id: question.id,
      answer: answers[question.id],
      question_text: question.question,
      question_type: question.type,
      difficulty: question.difficulty,
      topic: question.topic
    }));

    return {
      survey_id: surveyData.id,
      user_id: surveyData.user_id,
      subject: surveyData.subject,
      answers: formattedAnswers,
      completed_at: new Date().toISOString()
    };
  }
}

export default SurveyService;