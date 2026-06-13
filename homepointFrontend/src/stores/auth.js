import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { jwtDecode } from 'jwt-decode'
import api from '@/services/api'
import config from '@/config/env'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('jwt_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  // Decode user from token if user data not available
  const getUserFromToken = () => {
    if (!token.value) return null
    try {
      const decoded = jwtDecode(token.value)
      return {
        id: decoded.user_id,
        username: decoded.username,
        email: decoded.email,
        role: decoded.role || (decoded.is_staff ? 'staff' : 'customer'),
        is_staff: decoded.is_staff,
        is_superuser: decoded.is_superuser,
      }
    } catch (error) {
      console.error('Failed to decode token:', error)
      return null
    }
  }

  // Initialize user from token if not set
  if (!user.value && token.value) {
    user.value = getUserFromToken()
  }

  const isAuthenticated = computed(() => !!token.value)

  const login = async (accessToken, refreshTokenValue, userData = null) => {
    token.value = accessToken
    refreshToken.value = refreshTokenValue
    localStorage.setItem('jwt_token', accessToken)
    localStorage.setItem('refresh_token', refreshTokenValue)

    // If userData provided, use it; otherwise decode from token
    if (userData) {
      user.value = userData
      localStorage.setItem('user', JSON.stringify(userData))
    } else {
      user.value = getUserFromToken()
      if (user.value) {
        localStorage.setItem('user', JSON.stringify(user.value))
      }
    }
  }

  const logout = async () => {
    // Call logout endpoint to blacklist token
    if (refreshToken.value) {
      try {
        await api.post('/users/auth/logout/', { refresh: refreshToken.value })
      } catch (error) {
        console.error('Logout API call failed:', error)
        // Continue with local logout even if API call fails
      }
    }

    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('jwt_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await fetch(`${config.API_BASE_URL}/users/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken.value }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const data = await response.json()
      token.value = data.access
      localStorage.setItem('jwt_token', data.access)
      return data.access
    } catch (error) {
      // Refresh failed, logout user
      await logout()
      throw error
    }
  }

  const checkAuth = async () => {
    if (!token.value) {
      return false
    }

    try {
      // Check if token is expired
      const decoded = jwtDecode(token.value)
      const currentTime = Date.now() / 1000

      if (decoded.exp < currentTime) {
        // Token expired, try to refresh
        await refreshAccessToken()
        return true
      }

      // Token valid, optionally fetch fresh user data
      try {
        const userData = await api.get('/users/auth/profile/')
        user.value = userData
        localStorage.setItem('user', JSON.stringify(userData))
      } catch (error) {
        // If profile fetch fails, use token data
        console.warn('Failed to fetch user profile, using token data')
      }

      return true
    } catch (error) {
      console.error('Auth check failed:', error)
      await logout()
      return false
    }
  }

  const hasRole = (role) => {
    return user.value?.role === role
  }

  const isAdmin = computed(() => {
    return user.value?.role === 'admin' || user.value?.is_superuser === true
  })

  const isStaff = computed(() => {
    return user.value?.is_staff === true || ['admin', 'staff'].includes(user.value?.role)
  })

  return {
    token,
    refreshToken,
    user,
    isAuthenticated,
    isAdmin,
    isStaff,
    login,
    logout,
    refreshAccessToken,
    checkAuth,
    hasRole,
  }
})
