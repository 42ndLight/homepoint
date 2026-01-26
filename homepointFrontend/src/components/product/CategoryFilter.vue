<template>
  <div class="mb-4">
    <label class="block text-sm font-medium mb-2">Filter by Category</label>
    <Select
      v-model="selectedCategory"
      :options="categoryOptions"
      optionLabel="label"
      optionValue="value"
      placeholder="All Categories"
      class="w-full md:w-14rem"
      @change="$emit('change', selectedCategory)"
    />
  </div>
</template>

<script setup>
import Select from 'primevue/select'
import { ref, onMounted, watch } from 'vue'
import db from '@/db/index'

const props = defineProps({
  modelValue: {
    type: [Number, String, null],
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectedCategory = ref(props.modelValue)
const categoryOptions = ref([
  { label: 'All Categories', value: null },
])

// Watch for changes and emit update:modelValue for v-model binding
watch(selectedCategory, (newValue) => {
  emit('update:modelValue', newValue)
  emit('change', newValue)
})

// Watch for external changes to modelValue
watch(() => props.modelValue, (newValue) => {
  selectedCategory.value = newValue
})

onMounted(async () => {
  try {
    const categories = await db.categories.toArray()
    categoryOptions.value = [
      { label: 'All Categories', value: null },
      ...categories.map(cat => ({
        label: cat.name,
        value: cat.id,
      })),
    ]
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
})
</script>

