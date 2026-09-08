<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 bg-[url('/src/assets/img/gen_image.webp')]">
    <Card class="w-full max-w-md p-6 shadow-lg">
      <template #header>
        <h2 class="text-2xl font-bold text-center">Reset Password</h2>
      </template>
      <template #subtitle>
        <p class="text-center text-gray-500 mt-1">
          {{ success ? 'All done' : 'Enter your new password' }}
        </p>
      </template>

      <template #content>
        <div v-if="!success" class="mt-6 space-y-5">
          <div>
            <span class="block text-sm font-medium mb-1">New Password
            <Password
              v-model="newPassword"
              fluid
              toggleMask
              :feedback="true"
              placeholder="••••••••"
              @keyup.enter="handleResetPassword"
            /></span>
          </div>

          <div>
            <span class="block text-sm font-medium mb-1">Confirm New Password
            <Password
              v-model="confirmPassword"
              fluid
              toggleMask
              :feedback="false"
              placeholder="••••••••"
              @keyup.enter="handleResetPassword"
            /></span>
          </div>
        </div>

        <div v-else class="mt-6 text-center space-y-5">
           <i class="pi pi-check-circle text-green-500 text-5xl"></i>
           <p class="text-lg font-medium">Password Reset Successful</p>
           <p class="text-sm text-gray-500">You can now log in with your new password.</p>
        </div>

        <Message v-if="errorMessage" severity="error" :closable="false" class="mb-2 mt-4">
          {{ errorMessage }}
        </Message>
      </template>

      <template #footer>
        <div v-if="!success" class="flex gap-3">
          <Button label="Back" severity="secondary" class="w-1/3" @click="handleBack" />
          <Button label="Reset Password" class="w-2/3" :loading="loading" @click="handleResetPassword" />
        </div>
        <div v-else class="flex gap-3 mt-4">
           <Button label="Go to Login" class="w-full" @click="router.push('/login')" />
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import Card from 'primevue/card'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getErrorMessage } from '@/utils/errorHandler'
import config from '@/config/env'
import { usePasswordResetStore } from '@/stores/passwordReset'

const router = useRouter()
const resetStore = usePasswordResetStore()

// This screen only makes sense right after a successful OTP verification —
// bounce back to the start of the flow if there's no reset grant to use.
if (!resetStore.resetToken) {
  router.replace({ name: 'reset-password' })
}

const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')
const success = ref(false)

const handleBack = () => {
  resetStore.clear()
  router.push('/login')
}

const handleResetPassword = async () => {
  if (!newPassword.value || !confirmPassword.value) {
    errorMessage.value = 'Please enter and confirm your new password'
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(`${config.API_BASE_URL}/users/auth/password-reset/confirm/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reset_token: resetStore.resetToken,
        new_password: newPassword.value,
        confirm_password: confirmPassword.value,
      }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      if (data?.new_password) {
        const msg = Array.isArray(data.new_password) ? data.new_password.join(' ') : data.new_password
        throw new Error(msg)
      }
      if (data?.confirm_password) {
        const msg = Array.isArray(data.confirm_password) ? data.confirm_password.join(' ') : data.confirm_password
        throw new Error(msg)
      }
      // An expired/consumed reset grant means the OTP must be verified again.
      if (typeof data?.error === 'string' && data.error.toLowerCase().includes('expired')) {
        resetStore.clear()
        router.replace({ name: 'reset-password' })
        return
      }
      throw new Error(data?.error || data?.detail || 'Failed to reset password')
    }

    resetStore.clear()
    success.value = true
  } catch (err) {
    errorMessage.value = err.message || getErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>
