import QRCode from 'qrcode'

/**
 * Format receipt data for KRA eTIMS compliance
 */
export function formatReceiptData(order) {
  return {
    invoiceNumber: `INV-${String(order.id).padStart(6, '0')}-${new Date(order.created_at).getTime()}`,
    orderId: order.id,
    date: new Date(order.created_at).toLocaleDateString('en-KE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }),
    time: new Date(order.created_at).toLocaleTimeString('en-KE', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }),
    items: order.items || [],
    subtotal: parseFloat(order.total_amount) / 1.16, // Remove VAT to get subtotal
    vat: (parseFloat(order.total_amount) / 1.16) * 0.16,
    total: parseFloat(order.total_amount),
    phoneNumber: order.phone_number,
    deliveryLocation: order.delivery_location,
  }
}

/**
 * Generate QR code data URL for eTIMS receipt
 * Encodes critical order info as per KRA eTIMS format
 */
export async function generateQRCode(receiptData) {
  try {
    // KRA eTIMS format: JSON with essential receipt data
    const qrData = {
      inv: receiptData.invoiceNumber,
      tin: import.meta.env.VITE_STORE_TIN || '118184471', // Store TIN from env
      total: receiptData.total.toFixed(2),
      vat: receiptData.vat.toFixed(2),
      date: receiptData.date,
      time: receiptData.time,
    }

    const qrString = JSON.stringify(qrData)
    const qrImage = await QRCode.toDataURL(qrString, {
      errorCorrectionLevel: 'H',
      type: 'image/png',
      width: 200,
      margin: 1,
    })

    return qrImage
  } catch (err) {
    console.error('Error generating QR code:', err)
    return null
  }
}

/**
 * Format currency for display (KES)
 */
export function formatCurrency(amount) {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

/**
 * Format item quantity (supports decimal for meters, kg)
 */
export function formatQuantity(quantity, unitType = 'piece') {
  if (!unitType || unitType === 'piece') {
    return `${parseInt(quantity)}`
  }

  // For decimal units (meter, kg, sqm)
  return quantity % 1 === 0 ? `${parseInt(quantity)}` : quantity.toFixed(2)
}

/**
 * Get store information (prioritize localStorage, fallback to env or defaults)
 */
export function getStoreInfo() {
  const saved = localStorage.getItem('store_settings')
  if (saved) {
    try {
      return JSON.parse(saved)
    } catch (e) {
      console.error('Failed to parse saved store settings', e)
    }
  }

  return {
    name: import.meta.env.VITE_STORE_NAME || 'HOMEPOINT HARDWARE STORE',
    address: import.meta.env.VITE_STORE_ADDRESS || 'Nairobi, Kenya',
    tin: import.meta.env.VITE_STORE_TIN || '118184471',
    phone: import.meta.env.VITE_STORE_PHONE || '+254 700 000000',
    pin: 'A00XXXXXXXXX',
  }
}
