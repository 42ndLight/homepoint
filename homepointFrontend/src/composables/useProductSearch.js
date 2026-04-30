import { ref, computed } from 'vue'
import Fuse from 'fuse.js'
import { getSellableItems } from '@/services/dbService'

export const useProductSearch = () => {
  const searchQuery = ref('')
  const products = ref([])
  const fuse = ref(null)
  const loading = ref(false)

  // Initialize Fuse.js with sellable items
  const initializeSearch = async () => {
    loading.value = true
    try {
      products.value = await getSellableItems()
      
      // Configure Fuse.js options
      const options = {
        keys: [
          'name',
          'display_name',
          'sku',
          'item_code',
          'attributes',
        ],
        threshold: 0.3,
        includeScore: true,
        minMatchCharLength: 2,
      }

      fuse.value = new Fuse(products.value, options)
    } catch (error) {
      console.error('Failed to initialize search:', error)
    } finally {
      loading.value = false
    }
  }

  // Search results
  const searchResults = computed(() => {
    if (!searchQuery.value || searchQuery.value.trim() === '') {
      return []
    }

    if (!fuse.value) {
      return []
    }

    const results = fuse.value.search(searchQuery.value.trim())
    return results.map(result => ({
      ...result.item,
      score: result.score,
      matches: result.matches,
    }))
  })

  // Escape special regex characters
  const escapeRegex = (string) => {
    return string.replaceAll(/[.*+?^${}()|[\]\\]/g, '\\$&')
  }

  // Highlight matching text
  const highlightMatch = (text, query) => {
    if (!text || !query) return text

    const escapedQuery = escapeRegex(query)
    const regex = new RegExp(`(${escapedQuery})`, 'gi')
    return text.replace(regex, '<mark>$1</mark>')
  }

  return {
    searchQuery,
    products,
    searchResults,
    loading,
    initializeSearch,
    highlightMatch,
  }
}

