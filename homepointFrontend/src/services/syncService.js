import api from '@/services/api'
import db from '@/db/index'

const SYNC_INTERVAL_MS = 5 * 60 * 1000 // 5 minutes

/**
 * Normalize API response to array (handles paginated { results: [] } or plain array)
 */
function toArray(data) {
  if (!data) return []
  if (Array.isArray(data)) return data
  return data.results != null ? data.results : []
}

/**
 * Fetch all products, variants, inventory and categories from API and store in Dexie with timestamps.
 * Conflict resolution: server data overwrites local (last-write-wins). Offline edits to catalog
 * are not persisted back in this version; future enhancement could add a pendingChanges table.
 *
 * @returns {Promise<{ success: boolean, timestamp?: string, error?: string }>}
 */
export async function syncAll() {
  try {
    const [categories, products, variants, inventory] = await Promise.all([
      api.get('/products/categories/'),
      api.get('/products/products/'),
      api.get('/products/variants/'),
      api.get('/products/inventory/'),
    ])

    const now = new Date().toISOString()

    await Promise.all([
      db.categories.clear(),
      db.products.clear(),
      db.variants.clear(),
      db.inventory.clear(),
    ])

    const categoriesData = toArray(categories)
    await db.categories.bulkPut(
      categoriesData.map((cat) => ({
        id: cat.id,
        name: cat.name,
        slug: cat.slug,
        parent_id: cat.parent,
        description: cat.description,
      }))
    )

    const productsData = toArray(products)
    await db.products.bulkPut(
      productsData.map((prod) => ({
        id: prod.id,
        name: prod.name,
        slug: prod.slug,
        category_id: prod.category,
        base_price: prod.base_price,
        is_active: prod.is_active,
        description: prod.description,
      }))
    )

    const variantsData = toArray(variants)
    await db.variants.bulkPut(
      variantsData.map((variant) => ({
        id: variant.id,
        product_id: variant.product,
        sku: variant.sku,
        price: variant.price,
        unit_type: variant.unit_type,
        stock_threshold: variant.stock_threshold,
        attributes: variant.attributes || {},
      }))
    )

    const inventoryData = toArray(inventory)
    await db.inventory.bulkPut(
      inventoryData.map((inv) => ({
        id: inv.id,
        variant_id: inv.variant,
        quantity: inv.quantity,
        last_updated: inv.last_updated,
        location: inv.location || '',
      }))
    )

    await db.syncMetadata.put({ id: 1, table_name: 'all', last_sync: now })

    return { success: true, timestamp: now }
  } catch (error) {
    const message = error?.message || error?.detail || 'Sync failed'
    console.error('[syncService] syncAll failed:', error)
    return { success: false, error: message }
  }
}

/**
 * Get last sync timestamp from Dexie (for UI without running sync).
 * @returns {Promise<string|null>}
 */
export async function getLastSyncTimestamp() {
  try {
    const row = await db.syncMetadata.get(1)
    return row?.last_sync ?? null
  } catch (error) {
    console.error('[syncService] getLastSyncTimestamp failed:', error)
    return null
  }
}

let intervalId = null

/**
 * Start background sync: run once immediately, then every 5 minutes.
 * Only runs when online. Call the returned function to stop.
 *
 * @param {() => void} [onSyncComplete] - Called after each sync (success or failure) with result
 * @returns {() => void} stop function
 */
export function startBackgroundSync(onSyncComplete) {
  if (intervalId != null) {
    return () => {}
  }

  const run = async () => {
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      if (onSyncComplete) onSyncComplete({ success: false, error: 'Offline' })
      return
    }
    const result = await syncAll()
    if (onSyncComplete) onSyncComplete(result)
  }

  run()

  intervalId = setInterval(run, SYNC_INTERVAL_MS)

  return function stopBackgroundSync() {
    if (intervalId != null) {
      clearInterval(intervalId)
      intervalId = null
    }
  }
}

/**
 * Stop background sync (e.g. on logout). No-op if not started.
 */
export function stopBackgroundSync() {
  if (intervalId != null) {
    clearInterval(intervalId)
    intervalId = null
  }
}
