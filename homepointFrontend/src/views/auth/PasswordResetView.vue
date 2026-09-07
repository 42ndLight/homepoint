<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 bg-[url('/src/assets/img/gen_image.webp')]">
    <Card class="w-full max-w-md p-6 shadow-lg">
      <template #header>
        <h2 class="text-2xl font-bold text-center">Reset Password</h2>
      </template>
      <template #subtitle>
        <p class="text-center text-gray-500 mt-1">
          {{ step === 1 ? 'Enter your registered phone number' : 'Enter verification code and new password' }}
        </p>
      </template>

      <template #content>
        <div v-if="step === 1" class="mt-6 space-y-5">
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

        <div v-else-if="step === 2" class="mt-6 space-y-5">
          <p class="text-sm text-gray-600 text-center mb-4">
            An OTP has been sent to {{ phoneNumber }}
          </p>
          <div>
            <span class="block text-sm font-medium mb-1">6-digit OTP
            <InputText
              v-model="otp"
              fluid
              placeholder="123456"
            /></span>
          </div>
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
        <div v-if="step === 1" class="flex flex-col gap-3">
          <Button label="Request OTP" class="w-full" :loading="loading" @click="handleRequestOTP" />
          <Button label="Back to Login" class="w-full" severity="secondary" text @click="router.push('/login')" />
        </div>
        <div v-else-if="step === 2" class="flex gap-3">
          <Button label="Back" severity="secondary" class="w-1/3" @click="step = 1; errorMessage = ''" />
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
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getErrorMessage } from '@/utils/errorHandler'
import config from '@/config/env'

const step = ref(1)
const phoneNumber = ref('')
const otp = ref('')
const newPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')
const router = useRouter()

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
    
    // Always move to step 2 to prevent number enumeration
    step.value = 2
    otp.value = ''
    newPassword.value = ''
  } catch (err) {
    errorMessage.value = getErrorMessage(err)
  } finally {
    loading.value = false
  }
}

const handleResetPassword = async () => {
  if (!otp.value || !newPassword.value) {
    errorMessage.value = 'Please enter both the OTP and new password'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(`${config.API_BASE_URL}/users/auth/password-reset/confirm/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone_number: phoneNumber.value,
        otp: otp.value,
        new_password: newPassword.value
      }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new Error(data?.error || data?.detail || 'Failed to reset password')
    }

    step.value = 3
  } catch (err) {
    errorMessage.value = err.message || getErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>
