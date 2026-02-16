<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <Card class="w-full max-w-2xl p-6 shadow-lg">
      <template #header>
        <h2 class="text-2xl font-bold text-center">Create Staff Account</h2>
      </template>

      <template #subtitle>
        <p class="text-center text-gray-500 mt-1">
          Admins can create new staff or fundi accounts here. The new user will sign in from the login page.
        </p>
      </template>

      <template #content>
        <div class="mt-6 space-y-5">
          <Message
            v-if="errorMessage"
            severity="error"
            :closable="false"
            class="mb-2"
          >
            {{ errorMessage }}
          </Message>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1" for="username">Username</label>
              <InputText
                id="username"
                v-model.trim="form.username"
                class="w-full"
                :invalid="!!fieldErrors.username"
                placeholder="jdoe"
              />
              <small v-if="fieldErrors.username" class="p-error">{{ fieldErrors.username }}</small>
            </div>

            <div>
              <label class="block text-sm font-medium mb-1" for="email">Email</label>
              <InputText
                id="email"
                v-model.trim="form.email"
                type="email"
                class="w-full"
                :invalid="!!fieldErrors.email"
                placeholder="jdoe@example.com"
              />
              <small v-if="fieldErrors.email" class="p-error">{{ fieldErrors.email }}</small>
            </div>

            <div>
              <label class="block text-sm font-medium mb-1" for="phone">Phone Number</label>
              <InputText
                id="phone"
                v-model.trim="form.phone_number"
                class="w-full"
                :invalid="!!fieldErrors.phone_number"
                placeholder="+2547XXXXXXXX (or 07..., 2547...)"
              />
              <small class="text-gray-500 block">
                Kenyan format only. You can enter 07..., 2547..., or +2547... — it will be normalized.
              </small>
              <small v-if="fieldErrors.phone_number" class="p-error">{{ fieldErrors.phone_number }}</small>
            </div>

            <div>
              <label class="block text-sm font-medium mb-1" for="role">Role</label>
              <Dropdown
                id="role"
                v-model="form.role"
                :options="roleOptions"
                optionLabel="label"
                optionValue="value"
                class="w-full"
              />
              <small v-if="fieldErrors.role" class="p-error">{{ fieldErrors.role }}</small>
            </div>

            <div>
              <label class="block text-sm font-medium mb-1" for="first_name">First Name</label>
              <InputText
                id="first_name"
                v-model.trim="form.first_name"
                class="w-full"
                :invalid="!!fieldErrors.first_name"
              />
              <small v-if="fieldErrors.first_name" class="p-error">{{ fieldErrors.first_name }}</small>
            </div>

            <div>
              <label class="block text-sm font-medium mb-1" for="last_name">Last Name</label>
              <InputText
                id="last_name"
                v-model.trim="form.last_name"
                class="w-full"
                :invalid="!!fieldErrors.last_name"
              />
              <small v-if="fieldErrors.last_name" class="p-error">{{ fieldErrors.last_name }}</small>
            </div>

            <div>
              <label class="block text-sm font-medium mb-1" for="password">Password</label>
              <Password
                id="password"
                v-model="form.password"
                class="w-full"
                toggleMask
                :feedback="false"
                :invalid="!!fieldErrors.password"
              />
              <small v-if="fieldErrors.password" class="p-error">{{ fieldErrors.password }}</small>
            </div>

            <div>
              <label class="block text-sm font-medium mb-1" for="confirm_password">Confirm Password</label>
              <Password
                id="confirm_password"
                v-model="form.confirm_password"
                class="w-full"
                toggleMask
                :feedback="false"
                :invalid="!!fieldErrors.confirm_password"
              />
              <small v-if="fieldErrors.confirm_password" class="p-error">
                {{ fieldErrors.confirm_password }}
              </small>
            </div>
          </div>
        </div>
      </template>

      <template #footer>
        <div class="flex flex-col md:flex-row justify-between items-center gap-3 mt-4">
          <Button
            label="Back to Login"
            icon="pi pi-arrow-left"
            severity="secondary"
            class="w-full md:w-auto"
            outlined
            @click="goToLogin"
          />

          <Button
            label="Create Account"
            icon="pi pi-user-plus"
            class="w-full md:w-auto"
            :loading="loading"
            @click="handleSubmit"
          />
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Message from 'primevue/message'
import { useToast } from 'primevue/usetoast'
import { register as registerUser } from '@/services/authService'
import { getErrorMessage } from '@/utils/errorHandler'

const router = useRouter()
const toast = useToast()

const loading = ref(false)
const errorMessage = ref('')

const form = ref({
  username: '',
  email: '',
  phone_number: '',
  role: 'staff',
  first_name: '',
  last_name: '',
  password: '',
  confirm_password: '',
})

const fieldErrors = ref({
  username: '',
  email: '',
  phone_number: '',
  role: '',
  first_name: '',
  last_name: '',
  password: '',
  confirm_password: '',
})

// Roles aligned with User.ROLE_CHOICES on the backend
const roleOptions = [
  { label: 'Staff', value: 'staff' },
  { label: 'Admin', value: 'admin' },
  { label: 'Fundi', value: 'fundi' },
  // Intentionally omit 'customer' here since this page is for staff creation
]

const clearFieldErrors = () => {
  Object.keys(fieldErrors.value).forEach((key) => {
    fieldErrors.value[key] = ''
  })
}

const validateForm = () => {
  clearFieldErrors()
  errorMessage.value = ''

  let valid = true

  if (!form.value.username) {
    fieldErrors.value.username = 'Username is required'
    valid = false
  }
  if (!form.value.email) {
    fieldErrors.value.email = 'Email is required'
    valid = false
  }
  if (!form.value.phone_number) {
    fieldErrors.value.phone_number = 'Phone number is required'
    valid = false
  }
  if (!form.value.role) {
    fieldErrors.value.role = 'Role is required'
    valid = false
  }
  if (!form.value.password) {
    fieldErrors.value.password = 'Password is required'
    valid = false
  }
  if (!form.value.confirm_password) {
    fieldErrors.value.confirm_password = 'Please confirm the password'
    valid = false
  } else if (form.value.password !== form.value.confirm_password) {
    fieldErrors.value.confirm_password = 'Passwords do not match'
    valid = false
  }

  return valid
}

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  loading.value = true
  errorMessage.value = ''

  const payload = {
    username: form.value.username.trim(),
    email: form.value.email.trim(),
    phone_number: form.value.phone_number.trim(),
    password: form.value.password,
    role: form.value.role,
    first_name: form.value.first_name.trim(),
    last_name: form.value.last_name.trim(),
  }

  try {
    await registerUser(payload)

    toast.add({
      severity: 'success',
      summary: 'User created',
      detail: 'Account created successfully. Ask the user to log in.',
      life: 4000,
    })

    router.push('/login')
  } catch (error) {
    // Try to parse DRF validation errors
    const data = error.data

    if (data && typeof data === 'object') {
      let nonFieldMessage = ''

      Object.entries(data).forEach(([key, value]) => {
        const message = Array.isArray(value) ? value.join(' ') : String(value)
        if (key in fieldErrors.value) {
          fieldErrors.value[key] = message
        } else {
          nonFieldMessage = message
        }
      })

      errorMessage.value = nonFieldMessage || 'Please correct the highlighted errors.'
    } else {
      errorMessage.value = getErrorMessage(error)
    }
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

