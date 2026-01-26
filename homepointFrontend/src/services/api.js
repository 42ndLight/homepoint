import { getErrorMessage } from '@/utils/errorHandler'
import config from '@/config/env'

// Create a fetch wrapper with interceptors
class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL
    this.timeout = config.API_TIMEOUT
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    
    // Get token from localStorage to avoid circular dependency
    const token = localStorage.getItem('jwt_token')

    // Prepare headers
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    // Add authorization token if available
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    // Create abort controller for timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      // Handle 401 Unauthorized - token expired or invalid
      if (response.status === 401) {
        // Try to refresh token if refresh token exists
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          try {
            const refreshResponse = await fetch(`${this.baseURL}/users/auth/token/refresh/`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh: refreshToken }),
            })

            if (refreshResponse.ok) {
              const refreshData = await refreshResponse.json()
              // Update token in localStorage
              localStorage.setItem('jwt_token', refreshData.access)
              // Retry original request with new token
              // Create a new AbortController for the retry to avoid timeout issues
              const retryController = new AbortController()
              const retryTimeoutId = setTimeout(() => retryController.abort(), this.timeout)
              headers.Authorization = `Bearer ${refreshData.access}`
              try {
                const retryResponse = await fetch(url, {
                  ...options,
                  headers,
                  signal: retryController.signal,
                })
                clearTimeout(retryTimeoutId)
                return this.handleResponse(retryResponse)
              } catch (retryError) {
                clearTimeout(retryTimeoutId)
                throw retryError
              }
            }
          } catch (refreshError) {
            // Refresh failed, clear auth and redirect
            localStorage.removeItem('jwt_token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('user')
            window.location.href = '/login'
            throw new Error('Session expired. Please login again.')
          }
        } else {
          // No refresh token, clear auth and redirect
          localStorage.removeItem('jwt_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          window.location.href = '/login'
          throw new Error('Session expired. Please login again.')
        }
      }

      return this.handleResponse(response)
    } catch (error) {
      clearTimeout(timeoutId)
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout. Please try again.')
      }
      
      throw error
    }
  }

  async handleResponse(response) {
    const contentType = response.headers.get('content-type')
    const isJSON = contentType && contentType.includes('application/json')

    let data
    try {
      data = isJSON ? await response.json() : await response.text()
    } catch (error) {
      data = null
    }

    if (!response.ok) {
      const error = new Error(data?.detail || data?.message || `HTTP ${response.status}`)
      error.status = response.status
      error.data = data
      throw error
    }

    return data
  }

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' })
  }

  post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  patch(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' })
  }
}

// Create and export API client instance
const api = new APIClient(config.API_BASE_URL)

export default api

