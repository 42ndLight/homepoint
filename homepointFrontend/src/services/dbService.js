// services/dbService.js
import db from '@/db/index'
import api from '@/services/api'

// ---------------------------------------------------------------------------
// Sync  — one API call instead of four
// ---------------------------------------------------------------------------

/**
 * Pulls everything from /products/products/ in a single request.
 * The backend already nests category + variants, and strips secret fields
 * (cost_price, stock_quantity, stock_threshold) for non-staff users.
 * What arrives here is exactly what this user is allowed to see — no
 * client-side filtering needed.
 */
export const syncProducts = async () => {
  try {
    const response = await api.get('/products/products/')
    const productsData = response?.results ?? (Array.isArray(response) ? response : [])

    const products   = []
    const variants   = []
    const categories = new Map()  // deduplicate by id

    for (const prod of productsData) {
      const cat = prod.category_detail
      if (cat) {
        categories.set(cat.id, {
          id:          cat.id,
          name:        cat.name,
          slug:        cat.slug,
          parent_id:   cat.parent ?? null,
          description: cat.description ?? '',
        })
      }

      products.push({
        id:          prod.id,
        name:        prod.name,
        slug:        prod.slug,
        description: prod.description ?? '',
        base_price:  prod.base_price,
        is_active:   prod.is_active,
        image:       prod.image ?? null,
        category_id: prod.category?.id ?? null,
      })

      for (const v of (prod.variants ?? [])) {
        variants.push({
          id:               v.id,
          product_id:       prod.id,
          sku:              v.sku,
          item_code:        v.item_code ?? v.sku,
          price:            Number.parseFloat(v.price ?? 0),

          // Staff-only fields — null when stripped by backend
          cost_price:       v.cost_price      != null ? Number.parseFloat(v.cost_price) : null,
          stock_quantity:   v.stock_quantity   ?? null,
          stock_threshold:  v.stock_threshold  ?? null,

          // Always present — server computes this for all roles
          stock_status:     v.stock_status ?? 'in_stock',  // "in_stock" | "low_stock" | "out_of_stock"

          unit_type:         v.unit_type         ?? 'piece',
          unit_type_display: v.unit_type_display ?? 'Per Piece',
          attributes:        v.attributes        ?? {},
          tax_type:          v.tax_type           ?? 'A',
        })
      }
    }

    await db.transaction('rw', db.categories, db.products, db.variants, async () => {
      await Promise.all([db.categories.clear(), db.products.clear(), db.variants.clear()])
      await db.categories.bulkPut([...categories.values()])
      await db.products.bulkPut(products)
      await db.variants.bulkPut(variants)
    })

    const now = new Date().toISOString()
    await db.syncMetadata.put({ id: 1, table_name: 'all', last_sync: now })

    return { success: true, timestamp: now }
  } catch (error) {
    console.error('Sync failed:', error)
    throw error
  }
}

// ---------------------------------------------------------------------------
// Catalog view  — getProducts()
// Returns: products with nested variants (ProductCard / ProductCatalogView)
// ---------------------------------------------------------------------------

export const getProducts = async () => {
  try {
    const [products, variants, categories] = await Promise.all([
      db.products.toArray(),
      db.variants.toArray(),
      db.categories.toArray(),
    ])

    const categoryMap = new Map(categories.map(c => [c.id, c]))

    return products.map(product => ({
      ...product,
      category: categoryMap.get(product.category_id) ?? null,
      variants: variants.filter(v => v.product_id === product.id),
    }))
  } catch (error) {
    console.error('getProducts failed:', error)
    throw error
  }
}

// ---------------------------------------------------------------------------
// POS view  — getSellableItems()
// Returns: flat variant rows (PosItemCard / POSView)
// ---------------------------------------------------------------------------

export const getSellableItems = async () => {
  try {
    const [variants, products] = await Promise.all([
      db.variants.toArray(),
      db.products.toArray(),
    ])

    const productMap = new Map(products.map(p => [p.id, p]))

    return variants.map(variant => {
      const parent = productMap.get(variant.product_id)
      if (!parent) return null

      const attrSuffix  = Object.values(variant.attributes ?? {}).join(' • ')
      const displayName = attrSuffix ? `${parent.name} • ${attrSuffix}` : parent.name

      return {
        id:           variant.id,
        product_id:   variant.product_id,
        sku:          variant.sku,
        item_code:    variant.item_code,
        name:         parent.name,
        display_name: displayName.trim(),
        image:        parent.image ?? null,
        price:        variant.price,
        cost_price:   variant.cost_price,      // null for cashiers — POS won't show it
        stock_status:    variant.stock_status, // always safe to show
        stock_quantity:  variant.stock_quantity,   // null for cashiers
        stock_threshold: variant.stock_threshold,  // null for cashiers
        unit_type:         variant.unit_type,
        unit_type_display: variant.unit_type_display,
        attributes:        variant.attributes,
        tax_type:          variant.tax_type,
      }
    }).filter(Boolean)
  } catch (error) {
    console.error('getSellableItems failed:', error)
    throw error
  }
}

// ---------------------------------------------------------------------------
// Barcode scan
// ---------------------------------------------------------------------------

export const getProductBySKU = async (sku) => {
  try {
    const variant = await db.variants.where('sku').equals(sku).first()
    if (!variant) return null

    const parent = await db.products.get(variant.product_id)
    if (!parent) return null

    const attrSuffix = Object.values(variant.attributes ?? {}).join(' • ')

    return {
      ...variant,
      name:         parent.name,
      display_name: attrSuffix ? `${parent.name} • ${attrSuffix}` : parent.name,
      image:        parent.image ?? null,
    }
  } catch (error) {
    console.error('getProductBySKU failed:', error)
    return null
  }
}

// ---------------------------------------------------------------------------
// Local search
// ---------------------------------------------------------------------------

export const searchProducts = async (query) => {
  try {
    if (!query?.trim()) return getProducts()

    const term = query.toLowerCase().trim()

    const [matchedProducts, matchedVariants] = await Promise.all([
      db.products.filter(p =>
        p.name.toLowerCase().includes(term) ||
        p.description?.toLowerCase().includes(term)
      ).toArray(),
      db.variants.filter(v =>
        v.sku.toLowerCase().includes(term) ||
        v.item_code?.toLowerCase().includes(term)
      ).toArray(),
    ])

    const ids = new Set([
      ...matchedProducts.map(p => p.id),
      ...matchedVariants.map(v => v.product_id),
    ])

    const all = await getProducts()
    return all.filter(p => ids.has(p.id))
  } catch (error) {
    console.error('searchProducts failed:', error)
    throw error
  }
}

// ---------------------------------------------------------------------------
// Sync metadata
// ---------------------------------------------------------------------------

export const getSyncStatus = async () => {
  try {
    const metadata = await db.syncMetadata.get(1)
    return metadata?.last_sync ?? null
  } catch {
    return null
  }
}