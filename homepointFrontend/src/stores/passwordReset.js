import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// In-memory (not persisted) state shared across the password-reset request,
// OTP-verification, and new-password steps. Deliberately not written to
// localStorage — losing it on a full page reload forces the user back to
// the start of the flow, which is the safer default for a password reset.
export const usePasswordResetStore = defineStore('passwordReset', () => {
  const phoneNumber = ref('')
  const resendAvailableAt = ref(0) // epoch ms when the next OTP resend is allowed
  const resetToken = ref('')

  const setPhoneNumber = (value) => {
    phoneNumber.value = value
  }

  const setResendCooldown = (seconds) => {
    resendAvailableAt.value = Date.now() + Math.max(0, Number(seconds) || 0) * 1000
  }

  const setResetToken = (value) => {
    resetToken.value = value
  }

  const clear = () => {
    phoneNumber.value = ''
    resendAvailableAt.value = 0
    resetToken.value = ''
  }

  // Expose only the last 3 digits of the phone number, e.g. "**********123".
  const maskedPhone = computed(() => {
    const value = phoneNumber.value
    if (!value) return ''
    const visibleCount = 3
    if (value.length <= visibleCount) return value
    return '*'.repeat(value.length - visibleCount) + value.slice(-visibleCount)
  })

  return {
    phoneNumber,
    resendAvailableAt,
    resetToken,
    maskedPhone,
    setPhoneNumber,
    setResendCooldown,
    setResetToken,
    clear,
  }
})
