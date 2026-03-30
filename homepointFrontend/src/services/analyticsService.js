import api from './api'

class AnalyticsService {
  /**
   * Fetch sales analytics data for a date range
   * @param {string} startDate - Start date in YYYY-MM-DD format
   * @param {string} endDate - End date in YYYY-MM-DD format
   * @param {number} limit - Max number of top products (default 10)
   * @returns {Promise<Object>} Analytics data with daily revenue, top products, and summary
   */
  static async getSalesData(startDate, endDate, limit = 10) {
    try {
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      if (limit) params.append('limit', limit)

      const queryString = params.toString()
      const endpoint = `/reports/analytics/${queryString ? '?' + queryString : ''}`

      const data = await api.get(endpoint)
      return data
    } catch (error) {
      console.error('Failed to fetch analytics data:', error)
      throw error
    }
  }

  /**
   * Helper to format date to YYYY-MM-DD
   * @param {Date} date - Date object
   * @returns {string} Formatted date string
   */
  static formatDate(date) {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  /**
   * Get date range for last N days
   * @param {number} days - Number of days to go back
   * @returns {Object} Object with startDate and endDate in YYYY-MM-DD format
   */
  static getDateRangeLastDays(days) {
    const endDate = new Date()
    const startDate = new Date(endDate)
    startDate.setDate(startDate.getDate() - days)

    return {
      startDate: this.formatDate(startDate),
      endDate: this.formatDate(endDate),
    }
  }

  /**
   * Get date range for current month
   * @returns {Object} Object with startDate and endDate in YYYY-MM-DD format
   */
  static getDateRangeCurrentMonth() {
    const today = new Date()
    const startDate = new Date(today.getFullYear(), today.getMonth(), 1)
    const endDate = new Date()

    return {
      startDate: this.formatDate(startDate),
      endDate: this.formatDate(endDate),
    }
  }

  /**
   * Get date range for previous month
   * @returns {Object} Object with startDate and endDate in YYYY-MM-DD format
   */
  static getDateRangePreviousMonth() {
    const today = new Date()
    const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0)
    const lastMonthStart = new Date(lastMonthEnd.getFullYear(), lastMonthEnd.getMonth(), 1)

    return {
      startDate: this.formatDate(lastMonthStart),
      endDate: this.formatDate(lastMonthEnd),
    }
  }
}

export default AnalyticsService
