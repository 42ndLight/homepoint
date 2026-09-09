<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 bg-[url('/src/assets/img/gen_image.webp')]">
    <Card class="w-full max-w-md p-6 shadow-lg">
      <template #header>
        <h2 class="text-2xl font-bold text-center">Reset Password</h2>
      </template>
      <template #subtitle>
        <p class="text-center text-gray-500 mt-1">Enter your registered phone number</p>
      </template>

      <template #content>
        <div class="mt-6 space-y-5">
          <div>
            <span class="block text-sm font-medium mb-1">Phone Number
            <InputText
              v-model="phoneNumber"
              fluid
              placeholder="254XXXXXXXX"
              @keyup.enter="handleRequestOTP"
            /></span>
          </div>
        </div>

        <Message v-if="errorMessage" severity="error" :closable="false" class="mb-2 mt-4">
          {{ errorMessage }}
        </Message>
      </template>

      <template #footer>
        <div class="flex flex-col gap-3">
          <Button label="Request OTP" class="w-full" :loading="loading" @click="handleRequestOTP" />
          <Button label="Back to Login" class="w-full" severity="secondary" text @click="router.push('/login')" />
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getErrorMessage } from '@/utils/errorHandler'
import config from '@/config/env'
import { usePasswordResetStore } from '@/stores/passwordReset'

const phoneNumber = ref('')
const loading = ref(false)
const errorMessage = ref('')
const router = useRouter()
const resetStore = usePasswordResetStore()

const handleRequestOTP = async () => {
  if (!phoneNumber.value) {
    errorMessage.value = 'Please enter your phone number'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(`${config.API_BASE_URL}/users/auth/password-reset/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: phoneNumber.value }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      // An active resend cooldown from an earlier request still means an
      // OTP is out there — send the user on to verify it instead of
      // blocking them here.
      if (response.status === 429) {
        resetStore.setPhoneNumber(phoneNumber.value)
        if (data?.retry_after) {
          resetStore.setResendCooldown(data.retry_after)
        }
        router.push({ name: 'reset-password-verify' })
        return
      }

      if (data?.phone_number) {
        const msg = Array.isArray(data.phone_number) ? data.phone_number.join(' ') : data.phone_number
        throw new Error(msg)
      }
      throw new Error(data?.error || data?.detail || 'Failed to request OTP')
    }

    resetStore.setPhoneNumber(phoneNumber.value)
    resetStore.setResendCooldown(data?.retry_after || 180)
    router.push({ name: 'reset-password-verify' })
  } catch (err) {
    errorMessage.value = err.message || getErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>
