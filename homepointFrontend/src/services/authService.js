import api from '@/services/api'

/**
 * Register a new user via the Django Register endpoint.
 * Expects payload matching RegisterSerializer:
 * {
 *   username,
 *   email,
 *   phone_number,
 *   password,
 *   role,
 *   first_name,
 *   last_name
 * }
 */
export const register = (payload) => {
  return api.post('/users/auth/register/', payload)
}

