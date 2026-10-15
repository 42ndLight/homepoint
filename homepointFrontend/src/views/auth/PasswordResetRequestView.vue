<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 bg-[url('/src/assets/img/gen_image.webp')]">
    <Card class="w-full max-w-md p-6 shadow-lg">
      <template #header>
        <h2 class="text-2xl font-bold text-center">Reset Password</h2>
      </template>
      <template #subtitle>
        <p class="text-center text-gray-500 mt-1">Enter your registered phone number or email</p>
      </template>

      <template #content>
        <div class="mt-6 space-y-5">
          <div>
            <label for="identifier-input" class="block text-sm font-medium mb-1">
              Phone Number or Email
            </label>
            <InputText
              id="identifier-input"
              v-model="identifier"
              fluid
              placeholder="e.g. 0712345678 or user@example.com"
              @keyup.enter="handleRequestOTP"
            />
            <div v-if="identifier.trim()" class="mt-2 flex items-center gap-1.5 text-xs">
              <span
                v-if="detectedChannel === 'email'"
                class="inline-flex items-center gap-1 text-blue-600 font-medium"
              >
                <i class="pi pi-envelope text-xs"></i>
                OTP will be delivered via Email
              </span>
              <span
                v-else
                class="inline-flex items-center gap-1 text-emerald-600 font-medium"
              >
                <i class="pi pi-mobile text-xs"></i>
                OTP will be delivered via SMS
              </span>
            </div>
          </div>
        </div>

        <Message v-if="errorMessage" severity="error" :closable="false" class="mb-2 mt-4">
          {{ errorMessage }}
        </Message>
      </template>

      <template #footer>
        <div class="flex flex-col gap-3">
          <Button
            :label="submitButtonLabel"
            class="w-full"
            :loading="loading"
            @click="handleRequestOTP"
          />
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
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getErrorMessage } from '@/utils/errorHandler'
import config from '@/config/env'
import { usePasswordResetStore } from '@/stores/passwordReset'

const identifier = ref('')
const loading = ref(false)
const errorMessage = ref('')
const router = useRouter()
const resetStore = usePasswordResetStore()

const detectedChannel = computed(() => {
  const val = identifier.value.trim()
  return val.includes('@') ? 'email' : 'sms'
})

const submitButtonLabel = computed(() => {
  if (!identifier.value.trim()) return 'Request OTP'
  return detectedChannel.value === 'email' ? 'Send OTP via Email' : 'Send OTP via SMS'
})

const validateInput = (value) => {
  const val = value.trim()
  if (!val) {
    return 'Please enter your phone number or email address'
  }

  if (val.includes('@')) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(val)) {
      return 'Please enter a valid email address (e.g. user@example.com)'
    }
  } else {
    const digitsOnly = val.replace(/\s+/g, '')
    const phoneRegex = /^(\+?254|0)[17]\d{8}$/
    if (!phoneRegex.test(digitsOnly)) {
      return 'Please enter a valid Kenyan phone number (e.g. 0712345678 or +254712345678)'
    }
  }

  return null
}

const handleRequestOTP = async () => {
  const validationError = validateInput(identifier.value)
  if (validationError) {
    errorMessage.value = validationError
    return
  }

  loading.value = true
  errorMessage.value = ''
  const trimmed = identifier.value.trim()
  const channel = detectedChannel.value

  try {
    const response = await fetch(`${config.API_BASE_URL}/users/auth/password-reset/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier: trimmed, channel }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      // An active resend cooldown from an earlier request still means an
      // OTP is out there — send the user on to verify it instead of blocking them.
      if (response.status === 429) {
        resetStore.setIdentifier(trimmed, channel)
        if (data?.retry_after) {
          resetStore.setResendCooldown(data.retry_after)
        }
        router.push({ name: 'reset-password-verify' })
        return
      }

      const fieldError = data?.identifier || data?.phone_number || data?.email
      if (fieldError) {
        const msg = Array.isArray(fieldError) ? fieldError.join(' ') : fieldError
        throw new Error(msg)
      }
      throw new Error(data?.error || data?.detail || 'Failed to request OTP')
    }

    resetStore.setIdentifier(trimmed, data?.channel || channel)
    if (data?.recipient) {
      resetStore.setMaskedRecipient(data.recipient)
    }
    resetStore.setResendCooldown(data?.retry_after || 60)
    router.push({ name: 'reset-password-verify' })
  } catch (err) {
    errorMessage.value = err.message || getErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>
