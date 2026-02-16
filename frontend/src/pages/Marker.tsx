import { useEffect, useState } from 'react'
import { getMarker } from '../services/api'

export default function Marker() {
  const [markerUrl, setMarkerUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadMarker()
  }, [])

  const loadMarker = async () => {
    try {
      setLoading(true)
      setError(null)
      const blob = await getMarker()
      const url = URL.createObjectURL(blob)
      setMarkerUrl(url)
    } catch (err) {
      setError('Failed to load ArUco marker. Please try again.')
      console.error('Marker load error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePrint = () => {
    window.print()
  }

  const handleDownload = () => {
    if (markerUrl) {
      const link = document.createElement('a')
      link.href = markerUrl
      link.download = 'aruco-marker.png'
      link.click()
    }
  }

  return (
    <>
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          #printable-area,
          #printable-area * {
            visibility: visible;
          }
          #printable-area {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="no-print mb-6">
          <h1 className="text-3xl font-bold mb-4">ArUco Marker Template</h1>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h2 className="font-semibold text-blue-900 mb-2">📐 How to Use This Marker</h2>
            <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
              <li>Print this page (the marker will be centered and scaled appropriately)</li>
              <li>Place the printed marker near your structure for scale reference</li>
              <li>Ensure the marker is clearly visible and not obscured in your photo</li>
              <li>The app will automatically detect the marker and calibrate the scale</li>
            </ol>
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-xl text-gray-600">⏳ Loading marker...</div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
            <button
              onClick={loadMarker}
              className="ml-4 text-sm underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {markerUrl && (
          <>
            <div id="printable-area" className="bg-white p-8 rounded-lg border-2 border-gray-300">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-bold mb-2">Auto Structure Analysis</h2>
                <p className="text-lg text-gray-600">ArUco Calibration Marker</p>
                <p className="text-sm text-gray-500 mt-2">
                  Marker ID: 42 | Dictionary: 4x4_50 | Size: 6 inches (15.24 cm)
                </p>
              </div>

              <div className="flex justify-center items-center">
                <div className="border-4 border-black p-4 bg-white">
                  <img
                    src={markerUrl}
                    alt="ArUco Marker"
                    className="w-64 h-64 sm:w-96 sm:h-96"
                    style={{ imageRendering: 'pixelated' }}
                  />
                </div>
              </div>

              <div className="mt-8 text-center text-sm text-gray-600">
                <p>Print this page at 100% scale (no scaling)</p>
                <p className="mt-1">The marker outer edge should measure 6 inches (15.24 cm)</p>
              </div>
            </div>

            <div className="no-print mt-6 flex gap-4 justify-center">
              <button
                onClick={handlePrint}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                🖨️ Print Marker
              </button>
              <button
                onClick={handleDownload}
                className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition"
              >
                💾 Download PNG
              </button>
            </div>

            <div className="no-print mt-8 bg-gray-50 rounded-lg p-6">
              <h3 className="font-semibold text-lg mb-3">Tips for Best Results</h3>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Print on white paper with good contrast</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Ensure the marker is flat and not wrinkled</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Good lighting helps with detection accuracy</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Keep the marker within the camera frame</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Avoid shadows or glare on the marker</span>
                </li>
              </ul>
            </div>
          </>
        )}
      </div>
    </>
  )
}
