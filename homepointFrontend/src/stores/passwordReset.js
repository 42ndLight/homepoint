import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// In-memory (not persisted) state shared across the password-reset request,
// OTP-verification, and new-password steps. Deliberately not written to
// localStorage — losing it on a full page reload forces the user back to
// the start of the flow, which is the safer default for a password reset.
export const usePasswordResetStore = defineStore('passwordReset', () => {
  const identifier = ref('')
  const channel = ref('sms') // 'sms' | 'email'
  const maskedRecipient = ref('')
  const resendAvailableAt = ref(0) // epoch ms when the next OTP resend is allowed
  const resetToken = ref('')

  const setIdentifier = (value, ch = null) => {
    const val = (value || '').trim()
    identifier.value = val
    if (ch) {
      channel.value = ch
    } else {
      channel.value = val.includes('@') ? 'email' : 'sms'
    }
  }

  // Preserved for backward compatibility
  const setPhoneNumber = (value) => {
    setIdentifier(value, 'sms')
  }

  const setChannel = (value) => {
    channel.value = value
  }

  const setMaskedRecipient = (value) => {
    maskedRecipient.value = value || ''
  }

  const setResendCooldown = (seconds) => {
    resendAvailableAt.value = Date.now() + Math.max(0, Number(seconds) || 0) * 1000
  }

  const setResetToken = (value) => {
    resetToken.value = value
  }

  const clear = () => {
    identifier.value = ''
    channel.value = 'sms'
    maskedRecipient.value = ''
    resendAvailableAt.value = 0
    resetToken.value = ''
  }

  // Masked representation for display in UI
  const displayRecipient = computed(() => {
    if (maskedRecipient.value) {
      return maskedRecipient.value
    }
    const val = identifier.value
    if (!val) return ''

    if (channel.value === 'email' || val.includes('@')) {
      const parts = val.split('@')
      const local = parts[0]
      const domain = parts[1] || ''
      if (local.length <= 2) {
        return `${local[0] || ''}*@${domain}`
      }
      return `${local[0]}${'*'.repeat(Math.max(1, local.length - 2))}${local.slice(-1)}@${domain}`
    }

    const visibleCount = 3
    if (val.length <= visibleCount) return val
    return '*'.repeat(val.length - visibleCount) + val.slice(-visibleCount)
  })

  // Backward compatibility alias for phoneNumber & maskedPhone
  const phoneNumber = computed({
    get: () => identifier.value,
    set: (val) => setPhoneNumber(val),
  })

  const maskedPhone = computed(() => displayRecipient.value)

  return {
    identifier,
    channel,
    maskedRecipient,
    displayRecipient,
    phoneNumber,
    maskedPhone,
    resendAvailableAt,
    resetToken,
    setIdentifier,
    setPhoneNumber,
    setChannel,
    setMaskedRecipient,
    setResendCooldown,
    setResetToken,
    clear,
  }
})
