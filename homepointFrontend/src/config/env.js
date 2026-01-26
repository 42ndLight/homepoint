// Environment configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default {
  API_BASE_URL,
  API_TIMEOUT: 30000, // 30 seconds
}

