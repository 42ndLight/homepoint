<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 bg-[url('/src/assets/img/gen_image.webp')]">    
    <Card class="w-full max-w-md p-6 shadow-lg">
      <template #header>
        <h2 class="text-2xl font-bold text-center">Hardware Store POS</h2>
      </template>
      <template #subtitle>
        <p class="text-center text-gray-500 mt-1">{{ requiresOtp ? 'Enter verification code' : 'Sign in to continue' }}</p>
      </template>

      <template #content>
        <div v-if="!requiresOtp" class="mt-6 space-y-5">
          <div>
            <span class="block text-sm font-medium mb-1">Username
            <InputText
              v-model="username"
              fluid
              placeholder="staff username"
              @keyup.enter="handleLogin"
            /></span>
          </div>

          <div>
            <span class="block text-sm font-medium mb-1 flex justify-between">
              Password
              <router-link to="/reset-password" class="text-xs text-indigo-600 hover:text-indigo-500">Forgot Password?</router-link>
            </span>
            <Password
              v-model="password"
              fluid
              toggleMask
              :feedback="false"
              placeholder="••••••••"
              @keyup.enter="handleLogin"
            />
          </div>
        </div>

        <div v-else class="mt-6 space-y-5">
          <p class="text-sm text-gray-600 text-center mb-4">
            An OTP has been sent to {{ phoneNumber }}
          </p>
          <div class="flex justify-center">
            <OTPInput @update:otp="handleOtpUpdate" />
          </div>
        </div>

        <Message v-if="errorMessage" severity="error" :closable="false" class="mb-2 mt-4">
          {{ errorMessage }}
        </Message>
      </template>

      <template #footer>
        <Button v-if="!requiresOtp" label="Login" class="w-full" :loading="loading" @click="handleLogin" />
        <div v-else class="flex gap-3">
          <Button label="Back" severity="secondary" class="w-1/3" @click="requiresOtp = false; errorMessage = ''" />
          <Button label="Verify OTP" class="w-2/3" :loading="loading" @click="handleVerifyOtp" />
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import Card from 'primevue/card'
import Image from 'primevue/image'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import OTPInput from '@/components/OTPInput.vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage, APIError } from '@/utils/errorHandler'
import config from '@/config/env'

const username = ref('')
const password = ref('')
const otp = ref('')
const phoneNumber = ref('')
const requiresOtp = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const auth = useAuthStore()
const router = useRouter()

const proceedWithLogin = async (tokens) => {
  try {
    const tempToken = tokens.access
    const profileResponse = await fetch(`${config.API_BASE_URL}/users/auth/profile/`, {
      headers: {
        'Authorization': `Bearer ${tempToken}`,
      },
    })

    let userData = null
    if (profileResponse.ok) {
      const profileContentType = profileResponse.headers.get('content-type')
      if (profileContentType && profileContentType.includes('application/json')) {
        try {
          userData = await profileResponse.json()
        } catch (e) {
          // Keep userData as null
        }
      }
    }

    await auth.login(tokens.access, tokens.refresh, userData)

    const role = userData?.role || (auth.user?.role)
    if (role === 'admin' || auth.isAdmin) {
      router.push('/admin')
    } else if (['staff', 'cashier'].includes(role)) {
      router.push('/pos')
    } else {
      router.push('/catalog')
    }
  } catch (profileError) {
    await auth.login(tokens.access, tokens.refresh)
    router.push('/catalog')
  }
}

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = 'Please enter both username and password'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(`${config.API_BASE_URL}/users/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new APIError(
        data?.detail || data?.error || data?.message || `Server error (HTTP ${response.status})`,
        response.status,
        data
      )
    }

    if (data?.requires_otp) {
      requiresOtp.value = true
      phoneNumber.value = data.phone_number
      otp.value = ''
    } else {
      await proceedWithLogin(data)
    }
  } catch (err) {
    console.error('Login error:', err)
    errorMessage.value = getErrorMessage(err)
  } finally {
    loading.value = false
  }
}

const handleVerifyOtp = async () => {
  if (!otp.value) {
    errorMessage.value = 'Please enter the OTP'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(`${config.API_BASE_URL}/users/auth/token/verify-otp/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: phoneNumber.value, otp: otp.value }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new APIError(
        data?.detail || data?.error || data?.message || `Server error (HTTP ${response.status})`,
        response.status,
        data
      )
    }
    
    await proceedWithLogin(data)
  } catch (err) {
    console.error('OTP verification error:', err)
    errorMessage.value = getErrorMessage(err)
  } finally {
    loading.value = false
  }
}

const handleOtpUpdate = (otpValue) => {
  otp.value = otpValue
  handleVerifyOtp()
}
</script>
