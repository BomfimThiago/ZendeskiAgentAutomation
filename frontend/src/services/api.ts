/**
 * API service for MyAwesomeFakeCompany Chat Application
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  message: string;
  session_id: string;
  persona?: string;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Helper to check if response is JSON
   */
  private async parseResponse(response: Response): Promise<any> {
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error('Backend is not responding correctly. Please ensure the server is running.');
    }
    return response.json();
  }

  /**
   * Send a chat message to the AI assistant
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await this.parseResponse(response).catch(() => ({
          detail: `Server error: ${response.status}`
        }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }

      return this.parseResponse(response);
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Cannot connect to backend. Please check if the server is running on http://localhost:8000');
      }
      throw error;
    }
  }

  /**
   * Get the welcome message
   */
  async getWelcomeMessage(): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/ai/chat/hello`);

      if (!response.ok) {
        const error = await this.parseResponse(response).catch(() => ({
          detail: `Server error: ${response.status}`
        }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }

      return this.parseResponse(response);
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Cannot connect to backend. Please check if the server is running on http://localhost:8000');
      }
      throw error;
    }
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<{ status: string }> {
    try {
      // Construct health URL by removing /api/v1 path
      // this.baseUrl = "http://localhost:8000/api/v1"
      // healthUrl should be "http://localhost:8000/health"
      let healthUrl: string;

      if (this.baseUrl.includes('/api/v1')) {
        healthUrl = this.baseUrl.replace('/api/v1', '/health');
      } else if (this.baseUrl.includes('/api')) {
        healthUrl = this.baseUrl.replace('/api', '/health');
      } else {
        healthUrl = `${this.baseUrl}/health`;
      }

      const response = await fetch(healthUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }

      return this.parseResponse(response);
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Cannot connect to backend server');
      }
      throw error;
    }
  }
}

export const apiService = new ApiService();
