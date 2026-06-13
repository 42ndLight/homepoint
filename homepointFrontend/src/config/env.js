// Environment configuration
const API_BASE_URL = window.config?.API_BASE_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default {
  API_BASE_URL,
  API_TIMEOUT: 30000, // 30 seconds
  STORE_NAME: window.config?.STORE_NAME || import.meta.env.VITE_STORE_NAME || '',
  STORE_TIN: window.config?.STORE_TIN || import.meta.env.VITE_STORE_TIN || '',
  STORE_ADDRESS: window.config?.STORE_ADDRESS || import.meta.env.VITE_STORE_ADDRESS || '',
  STORE_PHONE: window.config?.STORE_PHONE || import.meta.env.VITE_STORE_PHONE || '',
}

