import db from '@/db/index'
import api from '@/services/api'

/**
 * Sync products, variants, categories, and inventory from API to Dexie
 */
export const syncProducts = async () => {
  try {
    // Fetch all data from API
    const [categories, products, variants, inventory] = await Promise.all([
      api.get('/products/categories/'),
      api.get('/products/products/'),
      api.get('/products/variants/'),
      api.get('/products/inventory/'),
    ])

    // Clear existing data (optional - you might want incremental updates)
    await Promise.all([
      db.categories.clear(),
      db.products.clear(),
      db.variants.clear(),
      db.inventory.clear(),
    ])

    // Insert categories
    if (categories && categories.results) {
      await db.categories.bulkPut(categories.results.map(cat => ({
        id: cat.id,
        name: cat.name,
        slug: cat.slug,
        parent_id: cat.parent,
        description: cat.description,
      })))
    } else if (Array.isArray(categories)) {
      await db.categories.bulkPut(categories.map(cat => ({
        id: cat.id,
        name: cat.name,
        slug: cat.slug,
        parent_id: cat.parent,
        description: cat.description,
      })))
    }

    // Insert products
    const productsData = products?.results || (Array.isArray(products) ? products : [])
    await db.products.bulkPut(productsData.map(prod => ({
      id: prod.id,
      name: prod.name,
      slug: prod.slug,
      category_id: prod.category,
      base_price: prod.base_price,
      is_active: prod.is_active,
      description: prod.description,
    })))

    // Insert variants
    const variantsData = variants?.results || (Array.isArray(variants) ? variants : [])
    await db.variants.bulkPut(variantsData.map(variant => ({
      id: variant.id,
      product_id: variant.product,
      sku: variant.sku,
      price: variant.price,
      unit_type: variant.unit_type,
      stock_threshold: variant.stock_threshold,
      attributes: variant.attributes || {},
    })))

    // Insert inventory
    const inventoryData = inventory?.results || (Array.isArray(inventory) ? inventory : [])
    await db.inventory.bulkPut(inventoryData.map(inv => ({
      id: inv.id,
      variant_id: inv.variant,
      quantity: inv.quantity,
      last_updated: inv.last_updated,
      location: inv.location || '',
    })))

    // Update sync metadata
    const now = new Date().toISOString()
    await db.syncMetadata.put({ id: 1, table_name: 'all', last_sync: now })

    return { success: true, timestamp: now }
  } catch (error) {
    console.error('Sync failed:', error)
    throw error
  }
}

/**
 * Get all products with their variants and inventory
 */
export const getProducts = async () => {
  try {
    const products = await db.products.toArray()
    const variants = await db.variants.toArray()
    const inventory = await db.inventory.toArray()
    const categories = await db.categories.toArray()

    // Create lookup maps
    const categoryMap = new Map(categories.map(c => [c.id, c]))
    const variantMap = new Map(variants.map(v => [v.id, v]))
    const inventoryMap = new Map(inventory.map(i => [i.variant_id, i]))

    // Enrich products with variants and inventory
    return products.map(product => {
      const productVariants = variants
        .filter(v => v.product_id === product.id)
        .map(variant => ({
          ...variant,
          inventory: inventoryMap.get(variant.id) || { quantity: 0 },
        }))

      return {
        ...product,
        category: categoryMap.get(product.category_id),
        variants: productVariants,
      }
    })
  } catch (error) {
    console.error('Failed to get products from DB:', error)
    throw error
  }
}


/**
 * Get flat, sellable variant rows — one row per variant.
 * Used by: POSView
 *
 * Each row is self-contained: has the parent product name, price,
 * stock quantity, and everything PosItemCard needs.
 */
export const getSellableItems = async () => {
  try {
    const [variants, inventory, products] = await Promise.all([
      db.variants.toArray(),
      db.inventory.toArray(),
      db.products.toArray(),
    ])

    const productMap  = new Map(products.map(p => [p.id, p]))
    const inventoryMap = new Map(inventory.map(i => [i.variant_id, i]))

    return variants.map(variant => {
      const parent = productMap.get(variant.product_id)
      if (!parent) return null // orphan variant — should not happen

      const inv = inventoryMap.get(variant.id) ?? { quantity: 0, is_low_stock: false }

      // Build a human-readable display name, e.g. "Steel Pipe • 6m"
      const attrSuffix = Object.values(variant.attributes ?? {}).join(' • ')
      const displayName = attrSuffix
        ? `${parent.name} • ${attrSuffix}`
        : parent.name

      return {
        // Identity
        id: variant.id,
        product_id: variant.product_id,
        sku: variant.sku,
        item_code: variant.item_code ?? variant.sku,

        // Display
        name: parent.name,
        display_name: displayName.trim(),
        image: parent.image ?? null,

        // Pricing
        price: parseFloat(variant.price ?? 0),

        // Unit info
        unit_type: variant.unit_type ?? 'piece',
        unit_type_display: variant.unit_type_display ?? 'Per Piece',

        // Attributes (size, colour, etc.)
        attributes: variant.attributes ?? {},

        // Stock
        stock_quantity: inv.quantity ?? 0,
        is_low_stock: inv.is_low_stock ?? (inv.quantity <= (variant.stock_threshold ?? 10)),
        stock_threshold: variant.stock_threshold ?? 10,

        // Tax
        tax_type: variant.tax_type ?? 'A',
      }
    }).filter(Boolean)
  } catch (error) {
    console.error('getSellableItems failed:', error)
    throw error
  }
}



/**
 * Search products locally using Dexie
 */
export const searchProducts = async (query) => {
  try {
    if (!query || query.trim() === '') {
      return await getProducts()
    }

    const searchTerm = query.toLowerCase().trim()
    
    // Search in products table
    const products = await db.products
      .filter(p => 
        p.name.toLowerCase().includes(searchTerm) ||
        p.description?.toLowerCase().includes(searchTerm)
      )
      .toArray()

    // Search in variants by SKU
    const variants = await db.variants
      .filter(v => v.sku.toLowerCase().includes(searchTerm))
      .toArray()

    // Get unique product IDs
    const productIds = new Set([
      ...products.map(p => p.id),
      ...variants.map(v => v.product_id),
    ])

    // Fetch full product data with variants
    const allProducts = await getProducts()
    return allProducts.filter(p => productIds.has(p.id))
  } catch (error) {
    console.error('Search failed:', error)
    throw error
  }
}

/**
 * Get product by SKU (for barcode scanning)
 */
export const getProductBySKU = async (sku) => {
  try {
    const variant = await db.variants.where('sku').equals(sku).first()
    if (!variant) return null

    const product = await db.products.get(variant.product_id)
    const inventory = await db.inventory.where('variant_id').equals(variant.id).first()

    return {
      ...product,
      variant: {
        ...variant,
        inventory: inventory || { quantity: 0 },
      },
    }
  } catch (error) {
    console.error('Failed to get product by SKU:', error)
    return null
  }
}

/**
 * Get sync status
 */
export const getSyncStatus = async () => {
  try {
    const metadata = await db.syncMetadata.get(1)
    return metadata ? metadata.last_sync : null
  } catch (error) {
    return null
  }
}

