// Centralized error handling utilities

export class APIError extends Error {
  constructor(message, status, data = null) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.data = data
  }
}

export const handleAPIError = (error) => {
  if (error instanceof APIError) {
    return {
      message: error.message,
      status: error.status,
      data: error.data,
    }
  }

  // Network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      message: 'Network error. Please check your connection.',
      status: 0,
      data: null,
    }
  }

  // Unknown errors
  return {
    message: error.message || 'An unexpected error occurred',
    status: 500,
    data: null,
  }
}

export const getErrorMessage = (error) => {
  const handled = handleAPIError(error)
  
  // Try to extract detail from Django REST Framework error format
  if (handled.data) {
    if (handled.data.detail) {
      return handled.data.detail
    }
    if (handled.data.message) {
      return handled.data.message
    }
    if (typeof handled.data === 'string') {
      return handled.data
    }
  }
  
  return handled.message
}

