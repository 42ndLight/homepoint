import { createRouter, createWebHistory } from 'vue-router'
import { requireAuth, requireRole, guestOnly } from './guards'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      beforeEnter: guestOnly,
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      // Only admins should be able to register new staff accounts
      beforeEnter: requireRole(['admin']),
      meta: { title: 'Register Staff' },
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('@/views/auth/PasswordResetRequestView.vue'),
      beforeEnter: guestOnly,
      meta: { title: 'Reset Password' },
    },
    {
      path: '/reset-password/verify',
      name: 'reset-password-verify',
      component: () => import('@/views/auth/PasswordResetVerifyView.vue'),
      beforeEnter: guestOnly,
      meta: { title: 'Verify Code' },
    },
    {
      path: '/reset-password/confirm',
      name: 'reset-password-confirm',
      component: () => import('@/views/auth/PasswordResetView.vue'),
      beforeEnter: guestOnly,
      meta: { title: 'Set New Password' },
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: () => import('@/views/PrivacyView.vue'),
      meta: { title: 'Privacy Policy' },
    },
    {
      path: '/pos',
      name: 'pos',
      component: () => import('@/views/pos/POSView.vue'),
      beforeEnter: requireRole(['staff', 'admin']),
      meta: { title: 'Point of Sale' },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/admin/AdminDashboardView.vue'),
      beforeEnter: requireRole(['admin']),
      meta: { title: 'Admin Dashboard' },
    },
    {
      path: '/admin/import',
      name: 'product-import',
      component: () => import('@/views/admin/ProductImportView.vue'),
      beforeEnter: requireRole(['admin']),
      meta: { title: 'Product Import' },
    },
    {
      path: '/catalog',
      name: 'catalog',
      component: () => import('@/views/catalog/ProductCatalogView.vue'),
      beforeEnter: requireAuth,
      meta: { title: 'Product Catalog' },
    },
    {
      path: '/receipt/:orderId',
      name: 'receipt',
      component: () => import('@/views/receipt/ReceiptView.vue'),
      beforeEnter: requireRole(['staff', 'admin']),
      meta: { title: 'Receipt' },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/components/UserProfile.vue'),
      beforeEnter: requireAuth,
      meta: { title: 'User Profile' },
    },
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/landing/LandingPage.vue'),
      beforeEnter: requireAuth,
      meta: { title: 'Internal Resources' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login',
    },
  ],
})

// Global navigation guard
router.beforeEach(async (to, from, next) => {
  // Set page title
  if (to.meta.title) {
    document.title = `${to.meta.title} - HomePoint POS`
  } else {
    document.title = 'HomePoint POS'
  }

  next()
})

export default router
