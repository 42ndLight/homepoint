import { ref, onMounted, onUnmounted, readonly } from 'vue'
import {
  syncAll,
  getLastSyncTimestamp,
  startBackgroundSync,
  stopBackgroundSync,
} from '@/services/syncService'

const isOnline = ref(
  typeof navigator !== 'undefined' ? navigator.onLine : true
)
const isSyncing = ref(false)
const lastSyncTime = ref(null)
const lastError = ref(null)

let stopSync = null

function setOnline(value) {
  isOnline.value = value
}

function setSyncing(value) {
  isSyncing.value = value
}

function onSyncComplete(result) {
  setSyncing(false)
  if (result.success) {
    lastSyncTime.value = result.timestamp
    lastError.value = null
  } else {
    lastError.value = result.error || 'Sync failed'
  }
}

/**
 * Reactive sync state and actions for inventory/catalog.
 * Use in App or layout to show sync status and run background sync when authenticated.
 */
export function useSync() {
  async function loadLastSyncFromDb() {
    const ts = await getLastSyncTimestamp()
    lastSyncTime.value = ts
  }

  /** Run sync once and update state. */
  async function syncNow() {
    if (!isOnline.value) {
      lastError.value = 'Offline'
      return { success: false, error: 'Offline' }
    }
    setSyncing(true)
    lastError.value = null
    const result = await syncAll()
    onSyncComplete(result)
    return result
  }

  /** Start background sync (on startup and every 5 min). Call once when user is authenticated. */
  function startPeriodicSync() {
    if (stopSync) return
    loadLastSyncFromDb()
    stopSync = startBackgroundSync(onSyncComplete)
  }

  /** Stop background sync (e.g. on logout). */
  function stopPeriodicSync() {
    if (stopSync) {
      stopSync()
      stopSync = null
    }
    stopBackgroundSync()
  }

  onMounted(() => {
    const handleOnline = () => setOnline(true)
    const handleOffline = () => setOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    onUnmounted(() => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    })
  })

  return {
    isOnline: readonly(isOnline),
    isSyncing: readonly(isSyncing),
    lastSyncTime: readonly(lastSyncTime),
    lastError: readonly(lastError),
    syncNow,
    startPeriodicSync,
    stopPeriodicSync,
    loadLastSyncFromDb,
  }
}
