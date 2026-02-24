<template>
  <Card v-if="authStore.user">
    <template #title>User Profile</template>
    <template #content>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Username
          <p class="text-gray-900">{{ authStore.user.username }}</p></label>
        </div>
        <div v-if="authStore.user.email">
          <label class="block text-sm font-medium text-gray-700 mb-1">Email
          <p class="text-gray-900">{{ authStore.user.email }}</p></label>
        </div>
        <div v-if="authStore.user.phone_number">
          <label class="block text-sm font-medium text-gray-700 mb-1">Phone Number
          <p class="text-gray-900">{{ authStore.user.phone_number }}</p></label>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Role
          <p class="text-gray-900 capitalize">{{ authStore.user.role }}</p></label>
        </div>
        <div v-if="authStore.user.first_name || authStore.user.last_name">
          <label class="block text-sm font-medium text-gray-700 mb-1">Name
          <p class="text-gray-900">{{ `${authStore.user.first_name || ''} ${authStore.user.last_name || ''}`.trim() }}</p></label>
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

