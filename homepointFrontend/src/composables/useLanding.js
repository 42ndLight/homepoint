import { ref } from 'vue'
import { getProducts, syncProducts } from '@/services/dbService'

/**
 * Fetch categories from synced database
 * Uses existing dbService which syncs from backend
 */
export function useCategories() {
  const fetchCategories = async () => {
    try {
      const products = await getProducts()
      
      // Extract unique categories from products
      const categoryMap = new Map()
      products.forEach((product) => {
        if (product.category_detail) {
          const cat = product.category_detail
          if (!categoryMap.has(cat.id)) {
            categoryMap.set(cat.id, {
              id: cat.id,
              name: cat.name,
              slug: cat.slug,
              image: product.image || null, // Use first product image as category image
              count: 0,
            })
          }
          categoryMap.get(cat.id).count += 1
        }
      })

      return Array.from(categoryMap.values())
    } catch (error) {
      console.error('Error fetching categories:', error)
      return []
    }
  }

  return { fetchCategories }
}

/**
 * Fetch products from synced database
 * Uses existing dbService which syncs from backend
 */
export function useProducts() {
  const fetchProducts = async (categoryId = null) => {
    try {
      const products = await getProducts()

      // Filter by category if provided
      if (categoryId) {
        return products.filter((p) => p.category_id === categoryId)
      }

      return products
    } catch (error) {
      console.error('Error fetching products:', error)
      throw error
    }
  }

  return { fetchProducts }
}

/**
 * Submit quote request
 */
export function useQuote() {
  const loading = ref(false)
  const error = ref(null)

  const submitQuote = async (quoteData) => {
    loading.value = true
    error.value = null

    try {
      // TODO: Implement actual quote submission to backend
      // const response = await fetch('/api/quotes/', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(quoteData),
      // })
      // if (!response.ok) throw new Error('Failed to submit quote')
      // return response.json()

      // For now: simulate success with console log
      console.log('Quote submitted:', quoteData)
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({ success: true, message: 'Quote request received!' })
        }, 500)
      })
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { submitQuote, loading, error }
}
