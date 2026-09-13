<template>
  <Card>
    <template #title>User Profile</template>
    <template #content>
      <form class="space-y-4" @submit.prevent="updateProfile">
        <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
        <Message v-if="success" severity="success" :closable="false">{{ success }}</Message>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label for="first-name" class="mb-1 block text-sm font-medium text-gray-700">First name</label>
            <InputText id="first-name" v-model.trim="form.first_name" class="w-full" :disabled="loading" />
          </div>
          <div>
            <label for="last-name" class="mb-1 block text-sm font-medium text-gray-700">Last name</label>
            <InputText id="last-name" v-model.trim="form.last_name" class="w-full" :disabled="loading" />
          </div>
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label for="username" class="mb-1 block text-sm font-medium text-gray-700">Username</label>
            <InputText id="username" v-model.trim="form.username" class="w-full" :disabled="loading" autocomplete="username" />
          </div>
          <div>
            <label for="email" class="mb-1 block text-sm font-medium text-gray-700">Email</label>
            <InputText id="email" v-model.trim="form.email" class="w-full" :disabled="loading" type="email" autocomplete="email" />
          </div>
          <div>
            <label for="phone-number" class="mb-1 block text-sm font-medium text-gray-700">Phone number</label>
            <InputText id="phone-number" v-model.trim="form.phone_number" class="w-full" :disabled="loading" type="tel" autocomplete="tel" />
          </div>
        </div>

        <Button type="submit" label="Save Profile" icon="pi pi-save" :loading="loading" />
      </form>
    </template>
  </Card>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { getErrorMessage } from '@/utils/errorHandler'

const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')
const success = ref('')
const form = reactive({
  username: '',
  email: '',
  phone_number: '',
  first_name: '',
  last_name: '',
})

const syncForm = () => {
  form.username = authStore.user?.username || ''
  form.email = authStore.user?.email || ''
  form.phone_number = authStore.user?.phone_number || ''
  form.first_name = authStore.user?.first_name || ''
  form.last_name = authStore.user?.last_name || ''
}

watch(() => authStore.user, syncForm, { immediate: true, deep: true })

const updateProfile = async () => {
  loading.value = true
  error.value = ''
  success.value = ''

  try {
    const user = await api.patch('/users/auth/profile/update/', form)
    authStore.user = user
    localStorage.setItem('user', JSON.stringify(user))
    success.value = 'Profile updated successfully.'
  } catch (requestError) {
    error.value = getErrorMessage(requestError)
  } finally {
    loading.value = false
  }
}
</script>
