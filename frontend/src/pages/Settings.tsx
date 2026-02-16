import { useState } from 'react'
import { getMarker } from '../services/api'

export default function Settings() {
  const [isDownloadingMarker, setIsDownloadingMarker] = useState(false)

  const handleDownloadMarker = async () => {
    setIsDownloadingMarker(true)
    try {
      const blob = await getMarker()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'aruco-marker.png'
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download marker:', err)
      alert('Failed to download marker. Please try again.')
    } finally {
      setIsDownloadingMarker(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Settings</h1>

      {/* ArUco Marker Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">📐 ArUco Marker</h2>
        <p className="text-gray-600 mb-4">
          Download the ArUco marker to use as a scale reference when capturing structures.
          Print it at actual size and place it near your structure for accurate measurements.
        </p>
        
        <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-4">
          <h3 className="font-semibold text-blue-900 mb-2">How to use:</h3>
          <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
            <li>Download and print the marker at 100% scale (no scaling)</li>
            <li>Place the marker near your structure where it's clearly visible</li>
            <li>Ensure the entire marker is visible in your photo</li>
            <li>The marker will be automatically detected for accurate scaling</li>
          </ol>
        </div>

        <button
          onClick={handleDownloadMarker}
          disabled={isDownloadingMarker}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:bg-gray-400"
        >
          {isDownloadingMarker ? '⏳ Downloading...' : '📥 Download Marker (PNG)'}
        </button>
      </div>

      {/* API Configuration */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">🔧 API Configuration</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              API Base URL
            </label>
            <input
              type="text"
              defaultValue={import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}
              disabled
              className="w-full px-3 py-2 border rounded bg-gray-50 text-gray-600"
            />
            <p className="text-xs text-gray-500 mt-1">
              Configure via VITE_API_URL environment variable
            </p>
          </div>
        </div>
      </div>

      {/* About */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">ℹ️ About</h2>
        <div className="space-y-2 text-gray-600">
          <p>
            <span className="font-semibold">Version:</span> 1.0.0
          </p>
          <p>
            <span className="font-semibold">Technology:</span> React + TypeScript + Vite + Tailwind CSS
          </p>
          <p>
            <span className="font-semibold">Analysis Engine:</span> Direct Stiffness Method
          </p>
          <p className="text-sm pt-4 border-t mt-4">
            Auto Structure Analysis uses computer vision to detect structural elements
            and applies classical structural analysis methods to compute member forces,
            reactions, and deflections.
          </p>
        </div>
      </div>
    </div>
  )
}
