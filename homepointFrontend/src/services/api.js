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
    const headers = this.prepareHeaders(options.headers)

    try {
      const response = await this.fetchWithTimeout(url, { ...options, headers })
      
      if (response.status === 401) {
        return await this.handleUnauthorized(url, options, headers)
      }

      return this.handleResponse(response)
    } catch (error) {
      return this.handleRequestError(error)
    }
  }

  prepareHeaders(customHeaders = {}) {
    const token = localStorage.getItem('jwt_token')
    const headers = {
      'Content-Type': 'application/json',
      ...customHeaders,
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    return headers
  }

  async fetchWithTimeout(url, options) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      return response
    } catch (error) {
      clearTimeout(timeoutId)
      throw error
    }
  }

  async handleUnauthorized(url, options, headers) {
    const refreshToken = localStorage.getItem('refresh_token')
    
    if (!refreshToken) {
      this.clearAuthAndRedirect()
      throw new Error('Session expired. Please login again.')
    }

    try {
      const newAccessToken = await this.refreshAccessToken(refreshToken)
      return await this.retryRequestWithNewToken(url, options, headers, newAccessToken)
    } catch (refreshError) {
      this.clearAuthAndRedirect()
      throw new Error('Session expired. Please login again.')
    }
  }

  async refreshAccessToken(refreshToken) {
    const refreshResponse = await fetch(`${this.baseURL}/users/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    })

    if (!refreshResponse.ok) {
      throw new Error('Token refresh failed')
    }

    const refreshData = await refreshResponse.json()
    localStorage.setItem('jwt_token', refreshData.access)
    return refreshData.access
  }

  async retryRequestWithNewToken(url, options, headers, newAccessToken) {
    const updatedHeaders = {
      ...headers,
      Authorization: `Bearer ${newAccessToken}`
    }

    const retryResponse = await this.fetchWithTimeout(url, {
      ...options,
      headers: updatedHeaders,
    })

    return this.handleResponse(retryResponse)
  }

  clearAuthAndRedirect() {
    localStorage.removeItem('jwt_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  handleRequestError(error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timeout. Please try again.')
    }
    throw error
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