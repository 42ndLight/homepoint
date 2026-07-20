<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100
      
      bg-[url('/src/assets/img/gen_image.webp')]">    
    <Card class="w-full max-w-md p-6 shadow-lg">
      <template #header>
        <h2 class="text-2xl font-bold text-center">Hardware Store POS</h2></template>
          <template #subtitle>
        <p class="text-center text-gray-500 mt-1">Sign in to continue</p>
              </template>

        <template #content>
        <div class="mt-6 space-y-5">
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
          <span class="block text-sm font-medium mb-1">Password
          <Password
            v-model="password"
            fluid
            toggleMask
            placeholder="••••••••"
            @keyup.enter="handleLogin"
          /></span>
        </div>

         <Message v-if="errorMessage" severity="error" :closable="false" class="mb-2">
          {{ errorMessage }}
        </Message>
        </div>
      </template>


      <template #footer>

        <Button label="Login" class="w-full" :loading="loading" @click="handleLogin" />


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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage, APIError } from '@/utils/errorHandler'
import config from '@/config/env'

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const auth = useAuthStore()
const router = useRouter()

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = 'Please enter both username and password'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    // Call login endpoint - note: this endpoint doesn't require auth, so we use fetch directly
    const response = await fetch(`${config.API_BASE_URL}/users/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    })

    const contentType = response.headers.get('content-type')
    const isJSON = contentType && contentType.includes('application/json')
    let data = null

    if (isJSON) {
      try {
        data = await response.json()
      } catch (e) {
        // Fallback if parsing fails
      }
    }

    if (!response.ok) {
      throw new APIError(
        data?.detail || data?.message || `Server error (HTTP ${response.status})`,
        response.status,
        data
      )
    }

    if (!data) {
      throw new APIError('Invalid server response format.', response.status)
    }

    // Backend returns {access, refresh} tokens
    // Fetch user profile to get role information
    try {
      // Temporarily set token to fetch profile
      const tempToken = data.access
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

      // Login with tokens and user data
      await auth.login(data.access, data.refresh, userData)

      // Redirect based on role
      const role = userData?.role || (auth.user?.role)
      if (role === 'admin' || auth.isAdmin) {
        router.push('/admin')
      } else if (['staff', 'cashier'].includes(role)) {
        router.push('/pos')
      } else {
        router.push('/catalog')
      }
    } catch (profileError) {
      // If profile fetch fails, still login with token data
      await auth.login(data.access, data.refresh)
      router.push('/catalog')
    }
  } catch (err) {
    console.error('Login error:', err)
    errorMessage.value = getErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>
