import { ref, onUnmounted } from 'vue'

// Dynamic import to avoid AMD/UMD bundling issues with Vite
let Quagga = null
const loadQuagga = async () => {
  if (!Quagga) {
    const module = await import('quagga')
    Quagga = module.default || module
  }
  return Quagga
}

/**
 * Composable for QuaggaJS barcode scanner
 * Handles init, start, stop, and detection callbacks
 *
 * @param {Object} options
 * @param {HTMLElement} options.target - DOM element to attach camera stream
 * @param {Function} options.onDetected - Callback when barcode is scanned (code: string)
 * @param {string[]} options.readers - Barcode reader formats (default: EAN, UPC, Code128)
 */
export function useBarcodeScanner(options = {}) {
  const { target, onDetected, readers = ['ean_reader', 'upc_reader', 'code_128_reader'] } = options

  const isScanning = ref(false)
  const error = ref(null)
  let detectionHandler = null

  const defaultConfig = {
    inputStream: {
      name: 'Live',
      type: 'LiveStream',
      target: target || null,
      constraints: {
        width: 640,
        height: 480,
        facingMode: 'environment',
      },
      area: {
        top: '10%',
        right: '10%',
        left: '10%',
        bottom: '10%',
      },
    },
    locator: {
      halfSample: true,
      patchSize: 'medium',
    },
    numOfWorkers: navigator.hardwareConcurrency || 4,
    frequency: 10,
    decoder: {
      readers,
    },
  }

  const init = async (configOverrides = {}) => {
    const Q = await loadQuagga()

    const config = {
      ...defaultConfig,
      ...configOverrides,
      inputStream: {
        ...defaultConfig.inputStream,
        ...(configOverrides?.inputStream || {}),
        target: configOverrides?.inputStream?.target ?? target ?? defaultConfig.inputStream.target,
      },
    }

    return new Promise((resolve, reject) => {
      Q.init(config, (err) => {
        if (err) {
          error.value = err
          isScanning.value = false
          reject(err)
          return
        }
        error.value = null
        resolve()
      })
    })
  }

  const start = async (configOverrides = {}) => {
    if (isScanning.value) return

    try {
      await init(configOverrides)
      isScanning.value = true

      detectionHandler = (result) => {
        const code = result?.codeResult?.code
        if (code && typeof onDetected === 'function') {
          onDetected(code)
        }
      }

      Quagga.onDetected(detectionHandler)
      Quagga.start()
    } catch (err) {
      error.value = err
      isScanning.value = false
      throw err
    }
  }

  const stop = () => {
    if (!isScanning.value) return

    try {
      if (Quagga) {
        if (detectionHandler) {
          Quagga.offDetected(detectionHandler)
          detectionHandler = null
        }
        Quagga.stop()
      }
    } catch (e) {
      console.warn('Error stopping Quagga:', e)
    } finally {
      isScanning.value = false
    }
  }

  onUnmounted(() => {
    stop()
  })

  return {
    isScanning,
    error,
    start,
    stop,
    init,
  }
}
