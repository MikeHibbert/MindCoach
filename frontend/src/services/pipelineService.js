import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

class PipelineService {
  /**
   * Start the LangChain content generation pipeline
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @returns {Promise<Object>} Pipeline start response
   */
  static async startContentGeneration(userId, subject) {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lessons/generate-langchain`
      );
      return response.data;
    } catch (error) {
      console.error('Error starting content generation:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get the status of a LangChain pipeline
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @param {string} pipelineId - Pipeline ID
   * @returns {Promise<Object>} Pipeline status response
   */
  static async getPipelineStatus(userId, subject, pipelineId) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lessons/pipeline-status/${pipelineId}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting pipeline status:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get curriculum scheme data
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @returns {Promise<Object>} Curriculum data
   */
  static async getCurriculumScheme(userId, subject) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/curriculum`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting curriculum scheme:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get lesson plans data
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @returns {Promise<Object>} Lesson plans data
   */
  static async getLessonPlans(userId, subject) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/users/${userId}/subjects/${subject}/lesson-plans`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting lesson plans:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Poll pipeline status with automatic retry
   * @param {string} userId - User ID
   * @param {string} subject - Subject name
   * @param {string} pipelineId - Pipeline ID
   * @param {Function} onUpdate - Callback for status updates
   * @param {Function} onComplete - Callback for completion
   * @param {Function} onError - Callback for errors
   * @param {number} pollInterval - Polling interval in milliseconds (default: 2000)
   */
  static pollPipelineStatus(userId, subject, pipelineId, onUpdate, onComplete, onError, pollInterval = 2000) {
    let pollCount = 0;
    const maxPolls = 300; // 10 minutes at 2-second intervals

    const poll = async () => {
      try {
        pollCount++;
        
        if (pollCount > maxPolls) {
          onError(new Error('Pipeline polling timeout - maximum polling time exceeded'));
          return;
        }

        const statusResponse = await this.getPipelineStatus(userId, subject, pipelineId);
        
        if (!statusResponse.success) {
          onError(new Error(statusResponse.message || 'Failed to get pipeline status'));
          return;
        }

        const status = statusResponse.pipeline_status;
        
        if (status.status === 'in_progress') {
          onUpdate(status);
          setTimeout(poll, pollInterval);
        } else if (status.status === 'completed') {
          onComplete(status);
        } else if (status.status === 'failed') {
          onError(new Error(status.error_message || 'Pipeline failed'));
        } else {
          // Handle other statuses (pending, etc.)
          onUpdate(status);
          setTimeout(poll, pollInterval);
        }
      } catch (error) {
        onError(error);
      }
    };

    poll();
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

export default PipelineService;