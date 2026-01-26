import { useAuthStore } from '@/stores/auth'

export const requireAuth = async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Check if user is authenticated
  if (!authStore.isAuthenticated) {
    // Try to check auth (will refresh token if needed)
    const isAuth = await authStore.checkAuth()
    if (!isAuth) {
      next({ name: 'login', query: { redirect: to.fullPath } })
      return
    }
  }

  next()
}

export const requireRole = (allowedRoles) => {
  return async (to, from, next) => {
    const authStore = useAuthStore()
    
    // First check authentication
    if (!authStore.isAuthenticated) {
      const isAuth = await authStore.checkAuth()
      if (!isAuth) {
        next({ name: 'login', query: { redirect: to.fullPath } })
        return
      }
    }

    // Check role
    const userRole = authStore.user?.role
    const isAdmin = authStore.isAdmin
    const isStaff = authStore.isStaff

    // Admin has access to everything
    if (isAdmin) {
      next()
      return
    }

    // Check if user has required role
    if (allowedRoles.includes(userRole) || (allowedRoles.includes('staff') && isStaff)) {
      next()
    } else {
      // Redirect to appropriate dashboard based on role
      if (isStaff) {
        next({ name: 'pos' })
      } else {
        next({ name: 'catalog' })
      }
    }
  }
}

export const guestOnly = (to, from, next) => {
  const authStore = useAuthStore()
  
  if (authStore.isAuthenticated) {
    // Redirect authenticated users to their dashboard
    const role = authStore.user?.role
    if (role === 'admin' || authStore.isAdmin) {
      next({ name: 'admin' })
    } else if (['staff', 'cashier'].includes(role)) {
      next({ name: 'pos' })
    } else {
      next({ name: 'catalog' })
    }
  } else {
    next()
  }
}

