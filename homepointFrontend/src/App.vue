<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Menubar from 'primevue/menubar'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import { computed } from 'vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()

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

const userMenuItems = [
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
      {
        separator: true,
      },
      {
        label: 'Logout',
        icon: 'pi pi-sign-out',
        command: handleLogout,
      },
    ],
  },
]
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation Bar -->
    <Menubar v-if="authStore.isAuthenticated && route.name !== 'login'" :model="menuItems" class="mb-4">
      <template #end>
        <Menubar :model="userMenuItems" />
      </template>
    </Menubar>

    <!-- Main Content -->
    <router-view />

    <!-- Toast Notifications -->
    <Toast />
  </div>
</template>

<style scoped></style>
