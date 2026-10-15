import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePasswordResetStore } from '../stores/passwordReset'

describe('Password Reset Store & Channel Handling', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with default clean state', () => {
    const store = usePasswordResetStore()
    expect(store.identifier).toBe('')
    expect(store.channel).toBe('sms')
    expect(store.maskedRecipient).toBe('')
    expect(store.displayRecipient).toBe('')
    expect(store.resetToken).toBe('')
    expect(store.resendAvailableAt).toBe(0)
  })

  it('correctly sets phone identifier and defaults channel to sms', () => {
    const store = usePasswordResetStore()
    store.setIdentifier('0712345678')

    expect(store.identifier).toBe('0712345678')
    expect(store.channel).toBe('sms')
    expect(store.phoneNumber).toBe('0712345678')
    expect(store.displayRecipient).toBe('*******678')
    expect(store.maskedPhone).toBe('*******678')
  })

  it('correctly sets email identifier and auto-detects email channel', () => {
    const store = usePasswordResetStore()
    store.setIdentifier('developer@example.com')

    expect(store.identifier).toBe('developer@example.com')
    expect(store.channel).toBe('email')
    expect(store.displayRecipient).toBe('d*******r@example.com')
  })

  it('honors explicitly specified channel', () => {
    const store = usePasswordResetStore()
    store.setIdentifier('user@example.com', 'email')
    expect(store.channel).toBe('email')

    store.setIdentifier('+254712345678', 'sms')
    expect(store.channel).toBe('sms')
  })

  it('uses masked recipient from server when available', () => {
    const store = usePasswordResetStore()
    store.setIdentifier('john.doe@domain.com', 'email')
    store.setMaskedRecipient('j***e@domain.com')

    expect(store.displayRecipient).toBe('j***e@domain.com')
  })

  it('sets and computes resend cooldown available timestamp', () => {
    const store = usePasswordResetStore()
    const now = Date.now()
    store.setResendCooldown(60)

    expect(store.resendAvailableAt).toBeGreaterThanOrEqual(now + 59000)
    expect(store.resendAvailableAt).toBeLessThanOrEqual(now + 61000)
  })

  it('clears all state on clear()', () => {
    const store = usePasswordResetStore()
    store.setIdentifier('user@example.com', 'email')
    store.setMaskedRecipient('u***r@example.com')
    store.setResetToken('test_token_123')
    store.setResendCooldown(60)

    store.clear()

    expect(store.identifier).toBe('')
    expect(store.channel).toBe('sms')
    expect(store.maskedRecipient).toBe('')
    expect(store.displayRecipient).toBe('')
    expect(store.resetToken).toBe('')
    expect(store.resendAvailableAt).toBe(0)
  })
})
