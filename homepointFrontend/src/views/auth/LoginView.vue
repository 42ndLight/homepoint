<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <Card class="w-full max-w-md p-6 shadow-lg">
      <template #header>
        <h2 class="text-2xl font-bold text-center">Hardware Store POS</h2>

        <p class="text-center text-gray-500 mt-1">Sign in to continue</p>

        <h1>Ken</h1>

        <div class="mt-6 space-y-5">
        <div>
          <label class="block text-sm font-medium mb-1">Username</label>
          <InputText 
            v-model="username" 
            class="w-full" 
            placeholder="staff username"
            @keyup.enter="handleLogin"
          />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Password</label>
          <Password 
            v-model="password" 
            class="w-full" 
            toggleMask 
            placeholder="••••••••"
            @keyup.enter="handleLogin"
          />
        </div>

         <Message v-if="errorMessage" severity="error" :closable="false" class="mb-2">
          {{ errorMessage }}
        </Message>

        <Button label="Login" class="w-full" :loading="loading" @click="handleLogin" />


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
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/utils/errorHandler'

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
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/users/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    })

    const data = await response.json()

    if (response.ok) {
      // Backend returns {access, refresh} tokens
      // Fetch user profile to get role information
      try {
        // Temporarily set token to fetch profile
        const tempToken = data.access
        const profileResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/users/auth/profile/`, {
          headers: {
            'Authorization': `Bearer ${tempToken}`,
          },
        })
        
        let userData = null
        if (profileResponse.ok) {
          userData = await profileResponse.json()
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
    } else {
      errorMessage.value = getErrorMessage({ message: data.detail || 'Login failed', status: response.status, data })
    }
  } catch (err) {
    console.error('Login error:', err)
    errorMessage.value = getErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>
