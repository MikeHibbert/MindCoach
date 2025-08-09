import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

class LessonService {
  /**
   * List all lessons for a user and subject
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @returns {Promise<Object>} Lesson list response
   */
  static async listLessons(userId, subject) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lessons`
      );
      return response.data;
    } catch (error) {
      console.error('Error listing lessons:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get a specific lesson by number
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @param {number} lessonNumber - Lesson number
   * @returns {Promise<Object>} Lesson data
   */
  static async getLesson(userId, subject, lessonNumber) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lessons/${lessonNumber}`
      );
      return response.data;
    } catch (error) {
      console.error(`Error getting lesson ${lessonNumber}:`, error);
      throw this.handleError(error);
    }
  }

  /**
   * Get lesson progress for a user and subject
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @returns {Promise<Object>} Progress data
   */
  static async getLessonProgress(userId, subject) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lessons/progress`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting lesson progress:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Generate lessons for a user and subject
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @returns {Promise<Object>} Generation result
   */
  static async generateLessons(userId, subject) {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lessons/generate`
      );
      return response.data;
    } catch (error) {
      console.error('Error generating lessons:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Mark a lesson as completed
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @param {number} lessonNumber - Lesson number
   * @returns {Promise<Object>} Completion result
   */
  static async markLessonCompleted(userId, subject, lessonNumber) {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lessons/${lessonNumber}/complete`
      );
      return response.data;
    } catch (error) {
      console.error(`Error marking lesson ${lessonNumber} as completed:`, error);
      throw this.handleError(error);
    }
  }

  /**
   * Get lesson completion status
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @returns {Promise<Object>} Completion status
   */
  static async getLessonCompletionStatus(userId, subject) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lessons/completion`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting lesson completion status:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Handle API errors and return user-friendly error objects
   * @param {Error} error - Axios error object
   * @returns {Error} Formatted error
   */
  static handleError(error) {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      const errorMessage = data?.message || 'An error occurred';
      const errorType = data?.error || 'unknown_error';
      
      const formattedError = new Error(errorMessage);
      formattedError.type = errorType;
      formattedError.status = status;
      formattedError.details = data?.details;
      
      return formattedError;
    } else if (error.request) {
      // Network error
      const networkError = new Error('Network error - please check your connection');
      networkError.type = 'network_error';
      return networkError;
    } else {
      // Other error
      return error;
    }
  }
}

export default LessonService;