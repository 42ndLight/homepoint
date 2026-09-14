<template>
  <Card v-if="authStore.isAdmin">
    <template #title>Staff Management</template>
    <template #content>
      <Message v-if="error" severity="error" :closable="false" class="mb-4">{{ error }}</Message>
      <div v-if="loading" class="py-4 text-center text-gray-600">Loading staff...</div>
      <div v-else-if="staffMembers.length === 0" class="py-4 text-center text-gray-600">No staff accounts found.</div>
      <div v-else class="divide-y divide-gray-200">
        <div v-for="staff in staffMembers" :key="staff.id" class="flex items-center justify-between gap-4 py-3">
          <div>
            <p class="font-medium text-gray-900">{{ staff.username }}</p>
            <p class="text-sm text-gray-600">{{ staff.first_name }} {{ staff.last_name }}</p>
            <p class="text-sm text-gray-600">{{ staff.email }} · {{ staff.phone_number }}</p>
          </div>
          <Button
            label="Delete"
            icon="pi pi-trash"
            severity="danger"
            outlined
            size="small"
            :loading="deletingStaffId === staff.id"
            :disabled="deletingStaffId !== null"
            @click="deleteStaff(staff)"
          />
        </div>
      </div>
    </template>
  </Card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { getErrorMessage } from '@/utils/errorHandler'

const authStore = useAuthStore()
const loading = ref(false)
const deletingStaffId = ref(null)
const error = ref('')
const staffMembers = ref([])

const loadStaff = async () => {
  if (!authStore.isAdmin) return

  loading.value = true
  error.value = ''

  try {
    const response = await api.get('/users/auth/staff/')
    const members = Array.isArray(response) ? response : response.results
    staffMembers.value = Array.isArray(members) ? members.filter(Boolean) : []
  } catch (requestError) {
    error.value = getErrorMessage(requestError)
  } finally {
    loading.value = false
  }
}

const deleteStaff = async (staff) => {
  if (!confirm(`Delete staff account "${staff.username}"? This cannot be undone.`)) return

  deletingStaffId.value = staff.id
  error.value = ''

  try {
    await api.delete(`/users/auth/staff/${staff.id}/`)
    staffMembers.value = staffMembers.value.filter(({ id }) => id !== staff.id)
  } catch (requestError) {
    error.value = getErrorMessage(requestError)
  } finally {
    deletingStaffId.value = null
  }
}

onMounted(loadStaff)
</script>
