import api from './api'

class FileImportService {
  /**
   * Upload XLSX file for import
   * @param {File} file - The XLSX file to upload
   * @returns {Promise<{task_id: string, status: string}>}
   */
  async uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)

    const url = `${api.baseURL}/api/files/`
    const token = localStorage.getItem('jwt_token')

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })

    if (!response.ok) {
      const error = new Error('Failed to upload file')
      error.status = response.status
      try {
        error.data = await response.json()
      } catch {
        error.data = null
      }
      throw error
    }

    return await response.json()
  }

  /**
   * Get the status of an import task
   * @param {string} taskId - The task ID from uploadFile
   * @returns {Promise<{task_id: string, status: string, error_msg: string, created_at: string, updated_at: string}>}
   */
  async getTaskStatus(taskId) {
    return api.get(`/api/tasks/${taskId}/`)
  }

  /**
   * Poll task status until completion
   * @param {string} taskId - The task ID
   * @param {number} pollInterval - Interval in ms (default 3000)
   * @param {number} maxAttempts - Max poll attempts (default 0 = infinite)
   * @returns {Promise<{task_id: string, status: string, ...}>}
   */
  pollTaskUntilComplete(taskId, pollInterval = 3000, maxAttempts = 0) {
    let attempts = 0
    let timerId = null
    let isCancelled = false

    const promise = new Promise((resolve, reject) => {
      const poll = async () => {
        if (isCancelled) {
          reject(new Error('Polling cancelled'))
          return
        }

        try {
          attempts++

          if (maxAttempts > 0 && attempts > maxAttempts) {
            reject(new Error('Task polling timeout'))
            return
          }

          const status = await this.getTaskStatus(taskId)

          if (status.status === 'COMPLETED' || status.status === 'FAILED') {
            resolve(status)
            return
          }

          // Still processing, schedule next poll
          timerId = setTimeout(poll, pollInterval)
        } catch (error) {
          // Network error during polling, retry
          timerId = setTimeout(poll, pollInterval)
        }
      }

      // Start polling
      poll()
    })

    return {
      promise,
      cancel: () => {
        isCancelled = true
        if (timerId) clearTimeout(timerId)
      }
    }
  }

  /**
   * Validate file before upload
   * @param {File} file - The file to validate
   * @returns {{valid: boolean, error: string | null}}
   */
  validateFile(file) {
    // Check file type
    if (!file.name.endsWith('.xlsx')) {
      return {
        valid: false,
        error: 'Only .xlsx files are accepted'
      }
    }

    // Check file size (10 MB max)
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'File size exceeds 10 MB limit'
      }
    }

    return {
      valid: true,
      error: null
    }
  }
}

export default new FileImportService()
