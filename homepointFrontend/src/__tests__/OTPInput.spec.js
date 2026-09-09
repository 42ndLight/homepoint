import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import OTPInput from '../components/OTPInput.vue'

describe('OTPInput', () => {
  it('moves focus forward after digit entry', async () => {
    const wrapper = mount(OTPInput, { attachTo: document.body })
    const inputs = wrapper.findAll('input')

    await inputs[0].trigger('keydown', { key: '1' })

    expect(document.activeElement).toBe(inputs[1].element)
  })

  it('moves focus to the previous input on backspace', async () => {
    const wrapper = mount(OTPInput, { attachTo: document.body })
    const inputs = wrapper.findAll('input')

    inputs[1].element.focus()
    await inputs[1].trigger('keydown', { key: 'Backspace' })

    expect(document.activeElement).toBe(inputs[0].element)
  })

  it('focuses the final input and emits a full pasted OTP', async () => {
    const wrapper = mount(OTPInput, { attachTo: document.body })
    const inputs = wrapper.findAll('input')

    await inputs[0].trigger('paste', {
      clipboardData: { getData: () => '123456' },
    })

    expect(document.activeElement).toBe(inputs[5].element)
    expect(wrapper.emitted('update:otp')).toEqual([['123456']])
  })
})
