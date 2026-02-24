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
    />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import Select from 'primevue/select'
import db from '@/db/index'

const props = defineProps({
  modelValue: {
    type: [Number, String, null],
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectedCategory = ref(props.modelValue)
const categoryOptions  = ref([{ label: 'All Categories', value: null }])

// Sync outward — one place emits both events
watch(selectedCategory, (val) => {
  emit('update:modelValue', val)
  emit('change', val)
})

// Sync inward — parent can reset the filter programmatically
watch(() => props.modelValue, (val) => {
  if (val !== selectedCategory.value) selectedCategory.value = val
})

onMounted(async () => {
  try {
    const categories = await db.categories.toArray()
    categoryOptions.value = [
      { label: 'All Categories', value: null },
      ...categories.map(c => ({ label: c.name, value: c.id })),
    ]
  } catch (err) {
    console.error('Failed to load categories:', err)
  }
})
</script>