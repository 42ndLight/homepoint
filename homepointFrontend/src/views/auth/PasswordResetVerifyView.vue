<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 bg-[url('/src/assets/img/gen_image.webp')]">
    <Card class="w-full max-w-md p-6 shadow-lg">
      <template #header>
        <h2 class="text-2xl font-bold text-center">Verify Code</h2>
      </template>
      <template #subtitle>
        <p class="text-center text-gray-500 mt-1">Enter the verification code sent to your phone</p>
      </template>

      <template #content>
        <div class="mt-6 space-y-5">
          <p class="text-sm text-gray-600 text-center mb-4">
            An OTP has been sent to {{ resetStore.maskedPhone }}
          </p>
          <div class="flex justify-center">
            <OTPInput :key="otpKey" @update:otp="handleOtpComplete" />
          </div>

          <div class="text-center">
            <Button
              :label="resendLabel"
              text
              size="small"
              :disabled="resendDisabled || resendLoading"
              :loading="resendLoading"
              @click="handleResendOTP"
            />
          </div>
        </div>

        <Message v-if="errorMessage" severity="error" :closable="false" class="mb-2 mt-4">
          {{ errorMessage }}
        </Message>
      </template>

      <template #footer>
        <div class="flex gap-3">
          <Button label="Back" severity="secondary" class="w-1/3" @click="handleBack" />
          <Button label="Verify OTP" class="w-2/3" :loading="loading" :disabled="!otp" @click="handleVerifyOtp" />
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import Card from 'primevue/card'
import Button from 'primevue/button'
import Message from 'primevue/message'
import OTPInput from '@/components/OTPInput.vue'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getErrorMessage } from '@/utils/errorHandler'
import config from '@/config/env'
import { usePasswordResetStore } from '@/stores/passwordReset'

const router = useRouter()
const resetStore = usePasswordResetStore()

// Don't allow reaching this screen without having requested an OTP first.
if (!resetStore.phoneNumber) {
  router.replace({ name: 'reset-password' })
}

const otp = ref('')
const otpKey = ref(0)
const loading = ref(false)
const resendLoading = ref(false)
const errorMessage = ref('')
const remainingSeconds = ref(0)

let timer = null
const tick = () => {
  const remainingMs = resetStore.resendAvailableAt - Date.now()
  remainingSeconds.value = remainingMs > 0 ? Math.ceil(remainingMs / 1000) : 0
}

onMounted(() => {
  tick()
  timer = setInterval(tick, 1000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const resendDisabled = computed(() => remainingSeconds.value > 0)
const resendLabel = computed(() =>
  resendDisabled.value ? `Resend code (${remainingSeconds.value}s)` : 'Resend code'
)

const handleOtpComplete = (otpValue) => {
  otp.value = otpValue
  errorMessage.value = ''
}

const handleBack = () => {
  resetStore.clear()
  router.push({ name: 'reset-password' })
}

const handleVerifyOtp = async () => {
  if (!otp.value) {
    errorMessage.value = 'Please enter the verification code'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(`${config.API_BASE_URL}/users/auth/password-reset/verify-otp/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: resetStore.phoneNumber, otp: otp.value }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      // Wrong or expired code — clear the input so the user can retype
      // without leaving this screen.
      otp.value = ''
      otpKey.value += 1
      throw new Error(data?.error || data?.detail || 'Invalid or expired OTP')
    }

    resetStore.setResetToken(data.reset_token)
    router.push({ name: 'reset-password-confirm' })
  } catch (err) {
    errorMessage.value = err.message || getErrorMessage(err)
  } finally {
    loading.value = false
  }
}

const handleResendOTP = async () => {
  if (resendDisabled.value) return

  resendLoading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(`${config.API_BASE_URL}/users/auth/password-reset/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: resetStore.phoneNumber }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      if (response.status === 429 && data?.retry_after) {
        resetStore.setResendCooldown(data.retry_after)
        tick()
      }
      throw new Error(data?.error || data?.detail || 'Failed to resend OTP')
    }

    resetStore.setResendCooldown(data?.retry_after || 60)
    tick()
    otp.value = ''
    otpKey.value += 1
  } catch (err) {
    errorMessage.value = err.message || getErrorMessage(err)
  } finally {
    resendLoading.value = false
  }
}
</script>
