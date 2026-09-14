<template>
  <Card>
    <template #title>Change Password</template>
    <template #content>
      <form class="space-y-4" @submit.prevent="changePassword">
        <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
        <Message v-if="success" severity="success" :closable="false">{{ success }}</Message>

        <div>
          <label for="old-password" class="mb-1 block text-sm font-medium text-gray-700">Current password</label>
          <Password id="old-password" v-model="form.old_password" class="w-full" :feedback="false" toggleMask :disabled="loading" />
        </div>
        <div>
          <label for="new-password" class="mb-1 block text-sm font-medium text-gray-700">New password</label>
          <Password id="new-password" v-model="form.new_password" class="w-full" toggleMask :disabled="loading" />
        </div>
        <div>
          <label for="confirm-password" class="mb-1 block text-sm font-medium text-gray-700">Confirm new password</label>
          <Password id="confirm-password" v-model="form.confirm_password" class="w-full" :feedback="false" toggleMask :disabled="loading" />
        </div>

        <Button type="submit" label="Change Password" icon="pi pi-lock" :loading="loading" />
      </form>
    </template>
  </Card>
</template>

<script setup>
import { reactive, ref } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'
import Password from 'primevue/password'
import api from '@/services/api'
import { getErrorMessage } from '@/utils/errorHandler'

const loading = ref(false)
const error = ref('')
const success = ref('')
const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const changePassword = async () => {
  loading.value = true
  error.value = ''
  success.value = ''

  try {
    await api.put('/users/auth/profile/update/password/', form)
    form.old_password = ''
    form.new_password = ''
    form.confirm_password = ''
    success.value = 'Password changed successfully.'
  } catch (requestError) {
    error.value = getErrorMessage(requestError)
  } finally {
    loading.value = false
  }
}
</script>
