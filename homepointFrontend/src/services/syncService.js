import api from '@/services/api'
import db from '@/db/index'
import { syncProducts } from '@/services/dbService'

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
  return await syncProducts()
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
