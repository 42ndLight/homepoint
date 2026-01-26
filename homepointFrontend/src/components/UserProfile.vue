<template>
  <Card v-if="authStore.user">
    <template #title>User Profile</template>
    <template #content>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <p class="text-gray-900">{{ authStore.user.username }}</p>
        </div>
        <div v-if="authStore.user.email">
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <p class="text-gray-900">{{ authStore.user.email }}</p>
        </div>
        <div v-if="authStore.user.phone_number">
          <label class="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
          <p class="text-gray-900">{{ authStore.user.phone_number }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Role</label>
          <p class="text-gray-900 capitalize">{{ authStore.user.role }}</p>
        </div>
        <div v-if="authStore.user.first_name || authStore.user.last_name">
          <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <p class="text-gray-900">{{ `${authStore.user.first_name || ''} ${authStore.user.last_name || ''}`.trim() }}</p>
        </div>
      </div>
    </template>
  </Card>
</template>

<script setup>
import Card from 'primevue/card'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

