<template>
  <div class="p-4 bg-white rounded-lg shadow-sm">
    <h2 class="text-xl font-bold text-gray-800 mb-6">Financial Transactions</h2>
    
    <div class="max-w-2xl">
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Transaction Type -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">Transaction Type</label>
          <div class="grid grid-cols-3 gap-3">
            <button
              type="button"
              v-for="type in transactionTypes"
              :key="type.value"
              @click="formData.transaction_type = type.value"
              :class="[
                'px-4 py-3 rounded-lg border-2 font-semibold transition flex flex-col items-center gap-2',
                formData.transaction_type === type.value
                  ? 'border-blue-600 bg-blue-50 text-blue-700'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300'
              ]"
            >
              <i :class="[type.icon, 'text-xl']"></i>
              {{ type.label }}
            </button>
          </div>
        </div>

        <!-- Amount -->
        <div>
          <label for="amount" class="block text-sm font-semibold text-gray-700 mb-2">Amount (KES)</label>
          <div class="relative">
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 font-bold">KES</span>
            <input
              id="amount"
              v-model.number="formData.amount"
              type="number"
              step="0.01"
              min="0"
              required
              class="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg font-bold"
              placeholder="0.00"
            />
          </div>
        </div>

        <!-- Expense Specific Fields -->
        <div v-if="formData.transaction_type === 'EXPENSE'" class="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in">
          <div>
            <label for="category" class="block text-sm font-semibold text-gray-700 mb-2">Category</label>
            <select
              id="category"
              v-model="formData.category"
              required
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="SUPPLIES">Supplies</option>
              <option value="UTILITIES">Utilities</option>
              <option value="SALARY">Salary</option>
              <option value="RENT">Rent</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
          <div>
            <label for="supplier" class="block text-sm font-semibold text-gray-700 mb-2">Supplier (Optional)</label>
            <input
              id="supplier"
              v-model="formData.supplier"
              type="text"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g. Kenya Power, Supplier Ltd"
            />
          </div>
        </div>

        <!-- Reference ID (Optional) -->
        <div>
          <label for="reference_id" class="block text-sm font-semibold text-gray-700 mb-2">Reference ID (Optional)</label>
          <input
            id="reference_id"
            v-model="formData.reference_id"
            type="text"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="e.g. Receipt #, Bank Trans ID"
          />
        </div>

        <!-- Notes -->
        <div>
          <label for="notes" class="block text-sm font-semibold text-gray-700 mb-2">Notes</label>
          <textarea
            id="notes"
            v-model="formData.notes"
            rows="3"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Details about this transaction..."
          ></textarea>
        </div>

        <!-- Submit Button -->
        <div class="pt-4">
          <button
            type="submit"
            :disabled="isSubmitting"
            class="w-full md:w-auto px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center justify-center gap-2 font-bold text-lg disabled:opacity-50"
          >
            <i class="pi pi-check" v-if="!isSubmitting"></i>
            <i class="pi pi-spin pi-spinner" v-else></i>
            {{ isSubmitting ? 'Recording...' : 'Record Transaction' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Info Alert -->
    <div class="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <h3 class="text-sm font-bold text-gray-700 mb-2">Quick Help:</h3>
      <ul class="text-xs text-gray-600 space-y-1 list-disc ml-4">
        <li><strong>Expense:</strong> Money spent on supplies, bills, etc. (Decreases CASH balance)</li>
        <li><strong>Deposit:</strong> Move physical CASH to the BANK account.</li>
        <li><strong>Withdrawal:</strong> Bring money from BANK to the CASH office.</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useToast } from 'primevue/usetoast'
import TransactionService from '@/services/transactionService'

const toast = useToast()
const isSubmitting = ref(false)

const transactionTypes = [
  { value: 'EXPENSE', label: 'Expense', icon: 'pi pi-shopping-bag' },
  { value: 'DEPOSIT', label: 'Deposit', icon: 'pi pi-arrow-up-right' },
  { value: 'WITHDRAWAL', label: 'Withdrawal', icon: 'pi pi-arrow-down-left' }
]

const initialFormState = {
  transaction_type: 'EXPENSE',
  amount: null,
  category: 'OTHER',
  supplier: '',
  reference_id: '',
  notes: ''
}

const formData = reactive({ ...initialFormState })

const handleSubmit = async () => {
  if (!formData.amount || formData.amount <= 0) {
    toast.add({ severity: 'warn', summary: 'Invalid Amount', detail: 'Please enter a valid amount', life: 3000 })
    return
  }

  isSubmitting.value = true
  try {
    await TransactionService.recordFinancialTransaction(formData)
    
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `${formData.transaction_type} recorded successfully`,
      life: 3000
    })

    // Reset form
    Object.assign(formData, initialFormState)
  } catch (err) {
    const errorDetail = err.response?.data?.detail || err.message || 'Failed to record transaction'
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: errorDetail,
      life: 5000
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
