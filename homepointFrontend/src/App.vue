<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Menubar from 'primevue/menubar'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import { computed, watch, onMounted } from 'vue'
import { useSync } from '@/composables/useSync'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()
const {
  isOnline,
  isSyncing,
  lastSyncTime,
  lastError,
  syncNow,
  startPeriodicSync,
  stopPeriodicSync,
} = useSync()

// Start background sync when authenticated; stop on logout
watch(
  () => authStore.isAuthenticated,
  (authenticated) => {
    if (authenticated) {
      startPeriodicSync()
    } else {
      stopPeriodicSync()
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (authStore.isAuthenticated) {
    startPeriodicSync()
  }
})

const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/login')
    toast.add({ severity: 'success', summary: 'Logged out', detail: 'You have been logged out successfully', life: 3000 })
  } catch (error) {
    console.error('Logout error:', error)
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to logout', life: 3000 })
  }
}

// Make menuItems reactive to auth state changes
const menuItems = computed(() => {
  const items = [
    {
      label: 'POS',
      icon: 'pi pi-shopping-cart',
      command: () => router.push('/pos'),
      visible: () => authStore.isStaff || authStore.isAdmin,
    },
    {
      label: 'Catalog',
      icon: 'pi pi-th-large',
      command: () => router.push('/catalog'),
      visible: () => authStore.isAuthenticated,
    },
    {
      label: 'Admin',
      icon: 'pi pi-cog',
      command: () => router.push('/admin'),
      visible: () => authStore.isAdmin,
    },
  ]
  return items.filter(item => !item.visible || item.visible())
})

// User menu (top-right), only show registration entry for admins
const userMenuItems = computed(() => {
  const items = [
    {
      label: authStore.user?.username || 'User',
      items: [
        {
          label: 'Profile',
          icon: 'pi pi-user',
          command: () => {
            // TODO: Navigate to profile page
            toast.add({ severity: 'info', summary: 'Coming soon', detail: 'Profile page coming soon', life: 3000 })
          },
        },
        // Admin-only registration link
        ...(authStore.isAdmin
          ? [
              {
                label: 'Register Staff',
                icon: 'pi pi-user-plus',
                command: () => router.push('/register'),
              },
              {
                separator: true,
              },
            ]
          : [
              {
                separator: true,
              },
            ]),
        {
          label: 'Logout',
          icon: 'pi pi-sign-out',
          command: handleLogout,
        },
      ],
    },
  ]

  return items
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation Bar -->
    <Menubar v-if="authStore.isAuthenticated && route.name !== 'login'" :model="menuItems" class="mb-4">
      <template #end>
        <div v-if="authStore.isAuthenticated" class="flex items-center gap-2 mr-3 text-sm" title="Sync status">
          <span class="flex items-center gap-1.5 px-2 py-1 rounded-full" :class="isOnline ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-600'">
            <i :class="['pi text-xs', isOnline ? 'pi-wifi' : 'pi-wifi-off']" />
            {{ isOnline ? 'Online' : 'Offline' }}
          </span>
          <span v-if="isSyncing" class="flex items-center gap-1 text-amber-600"><i class="pi pi-spin pi-spinner text-xs" /> Syncing…</span>
          <span v-else-if="lastSyncTime" class="text-gray-500" :title="'Last sync: ' + lastSyncTime">Synced</span>
          <span v-else-if="lastError" class="text-red-600 cursor-pointer" :title="lastError" @click="syncNow()">Error</span>
        </div>
        <Menubar :model="userMenuItems" />
      </template>
    </Menubar>

    <!-- Main Content -->
    <router-view />

    <!-- Toast Notifications -->
    <Toast />
  </div>
</template>

