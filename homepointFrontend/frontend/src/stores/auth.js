import { defineStore } from 'pinia'
import axios from 'axios'

axios.defaults.baseURL = 'http://localhost:8000/'  

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: localStorage.getItem('access') || null,
    refreshToken: localStorage.getItem('refresh') || null,
  }),
  actions: {
    async login(phone, password) {
      try {
        const res = await axios.post('auth/login/', { phone_number: phone, password })
        this.accessToken = res.data.access
        this.refreshToken = res.data.refresh
        this.user = res.data.user
        localStorage.setItem('access', this.accessToken)
        localStorage.setItem('refresh', this.refreshToken)
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
        return { success: true }
      } catch (err) {
        return { success: false, error: err.response?.data || 'Login failed' }
      }
    },
    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      delete axios.defaults.headers.common['Authorization']
    },
    loadFromStorage() {
      if (this.accessToken) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
        // Optionally fetch profile to set user
      }
    }
  }
})