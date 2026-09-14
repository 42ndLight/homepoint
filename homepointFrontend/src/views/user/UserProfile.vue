<template>
  <div v-if="authStore.user" class="mx-auto w-full max-w-3xl space-y-6 p-6">
    <ProfileDetailsForm />
    <ChangePasswordForm />
    <StaffManagement />
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import ChangePasswordForm from '@/components/user/ChangePasswordForm.vue'
import ProfileDetailsForm from '@/components/user/ProfileDetailsForm.vue'
import StaffManagement from '@/components/user/StaffManagement.vue'

const authStore = useAuthStore()
</script>
