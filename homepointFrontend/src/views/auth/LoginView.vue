<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 bg-[url('/src/assets/img/gen_image.webp')]">
    <Card class="w-full max-w-md p-6 shadow-lg">
      <template #header>
        <h2 class="text-2xl font-bold text-center">Hardware Store POS</h2>
      </template>
      <template #subtitle>
        <p class="text-center text-gray-500 mt-1">Sign in to continue</p>
      </template>

      <template #content>
        <div class="mt-6 space-y-5">
          <div>
            <span class="block text-sm font-medium mb-1">
              Username
              <InputText
                v-model="username"
                fluid
                placeholder="staff username"
                @keyup.enter="handleLogin"
              />
            </span>
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

        <Message v-if="errorMessage" severity="error" :closable="false" class="mb-2 mt-4">
          {{ errorMessage }}
        </Message>
      </template>

      <template #footer>
        <Button label="Login" class="w-full" :loading="loading" @click="handleLogin" />
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import config from '@/config/env'
import { APIError, getErrorMessage } from '@/utils/errorHandler'

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const auth = useAuthStore()
const router = useRouter()

const proceedWithLogin = async (tokens) => {
  try {
    const profileResponse = await fetch(`${config.API_BASE_URL}/users/auth/profile/`, {
      headers: {
        Authorization: `Bearer ${tokens.access}`,
      },
    })

    const userData = profileResponse.ok ? await profileResponse.json() : null
    await auth.login(tokens.access, tokens.refresh, userData)

    const role = userData?.role || auth.user?.role
    if (role === 'admin' || auth.isAdmin) {
      router.push('/admin')
    } else if (['staff', 'cashier'].includes(role)) {
      router.push('/pos')
    } else {
      router.push('/catalog')
    }
  } catch {
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

    await proceedWithLogin(data)
  } catch (error) {
    console.error('Login error:', error)
    errorMessage.value = getErrorMessage(error)
  } finally {
    loading.value = false
  }
}
</script>
