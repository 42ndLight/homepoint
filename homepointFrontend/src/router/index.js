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
      // beforeEnter: requireRole(['admin']),
      meta: { title: 'Register Staff' },
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
      path: '/',
      name: 'landing',
      component: () => import('@/views/landing/LandingPage.vue'),
      meta: { title: 'Homepoint Hardware Store' },
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
