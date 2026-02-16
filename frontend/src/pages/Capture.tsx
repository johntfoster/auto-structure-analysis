import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeImage } from '../services/api'

type CaptureMode = 'initial' | 'camera' | 'preview' | 'annotate'

export default function Capture() {
  const navigate = useNavigate()
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imagePreviewRef = useRef<HTMLImageElement>(null)
  const annotateCanvasRef = useRef<HTMLCanvasElement>(null)
  
  const [mode, setMode] = useState<CaptureMode>('initial')
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [capturedImage, setCapturedImage] = useState<string | null>(null)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [markerPosition, setMarkerPosition] = useState<{ x: number; y: number } | null>(null)
  const [manualScale, setManualScale] = useState<string>('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showMarkerModal, setShowMarkerModal] = useState(false)

  // Cleanup video stream on unmount
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [stream])

  const startCamera = async () => {
    try {
      setError(null)
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false,
      })
      setStream(mediaStream)
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
      }
      setMode('camera')
    } catch (err) {
      setError('Could not access camera. Please check permissions or use file upload.')
      console.error('Camera error:', err)
    }
  }

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
    setMode('initial')
  }

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current
      const canvas = canvasRef.current
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      if (ctx) {
        ctx.drawImage(video, 0, 0)
        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], `capture-${Date.now()}.jpg`, { type: 'image/jpeg' })
            setImageFile(file)
            setCapturedImage(canvas.toDataURL('image/jpeg'))
            stopCamera()
            setMode('preview')
          }
        }, 'image/jpeg', 0.95)
      }
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setImageFile(file)
      const reader = new FileReader()
      reader.onload = (event) => {
        setCapturedImage(event.target?.result as string)
        setMode('preview')
      }
      reader.readAsDataURL(file)
    }
  }

  const proceedToAnnotation = () => {
    setMode('annotate')
  }

  const retake = () => {
    setCapturedImage(null)
    setImageFile(null)
    setMarkerPosition(null)
    setManualScale('')
    setMode('initial')
  }

  // Handle marker position click on annotation canvas
  useEffect(() => {
    if (mode === 'annotate' && annotateCanvasRef.current && imagePreviewRef.current) {
      const canvas = annotateCanvasRef.current
      const img = imagePreviewRef.current
      
      // Set canvas to match image dimensions
      canvas.width = img.naturalWidth
      canvas.height = img.naturalHeight
      
      const ctx = canvas.getContext('2d')
      if (ctx) {
        // Draw the image
        ctx.drawImage(img, 0, 0)
        
        // Draw marker if set
        if (markerPosition) {
          drawMarker(ctx, markerPosition.x, markerPosition.y)
        }
      }
    }
  }, [mode, capturedImage, markerPosition])

  const drawMarker = (ctx: CanvasRenderingContext2D, x: number, y: number) => {
    ctx.strokeStyle = '#3B82F6'
    ctx.fillStyle = '#3B82F6'
    ctx.lineWidth = 3
    
    // Draw crosshair
    ctx.beginPath()
    ctx.moveTo(x - 20, y)
    ctx.lineTo(x + 20, y)
    ctx.moveTo(x, y - 20)
    ctx.lineTo(x, y + 20)
    ctx.stroke()
    
    // Draw circle
    ctx.beginPath()
    ctx.arc(x, y, 15, 0, Math.PI * 2)
    ctx.stroke()
    
    // Draw label
    ctx.fillStyle = '#3B82F6'
    ctx.font = 'bold 14px sans-serif'
    ctx.fillText('ArUco Marker', x + 25, y - 10)
  }

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = annotateCanvasRef.current
    if (!canvas) return
    
    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY
    
    setMarkerPosition({ x, y })
  }

  const handleAnalyze = async () => {
    if (!imageFile) return
    
    setIsAnalyzing(true)
    setError(null)
    
    try {
      const result = await analyzeImage({
        image: imageFile,
        marker_position: markerPosition ?? undefined,
        manual_scale: manualScale ? parseFloat(manualScale) : undefined,
      })
      
      navigate(`/analyze/${result.id}`)
    } catch (err) {
      setError('Analysis failed. Please try again or check your image.')
      console.error('Analysis error:', err)
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Capture Structure</h1>
        <button
          onClick={() => setShowMarkerModal(true)}
          className="text-blue-600 hover:text-blue-700 text-sm font-medium"
        >
          📐 Download ArUco Marker
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Initial Mode */}
      {mode === 'initial' && (
        <div className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
            <div className="mb-6">
              <svg className="mx-auto h-24 w-24 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-2">Take a Photo or Upload</h2>
            <p className="text-gray-600 mb-6">
              Capture a truss structure with an ArUco marker for scale reference
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={startCamera}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                📷 Open Camera
              </button>
              <label className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition cursor-pointer">
                📁 Upload from Device
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Camera Mode */}
      {mode === 'camera' && (
        <div className="space-y-4">
          <div className="relative bg-black rounded-lg overflow-hidden">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="w-full"
            />
            <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-4">
              <button
                onClick={capturePhoto}
                className="bg-blue-600 text-white px-8 py-3 rounded-full font-semibold hover:bg-blue-700 transition shadow-lg"
              >
                📸 Capture
              </button>
              <button
                onClick={stopCamera}
                className="bg-gray-600 text-white px-6 py-3 rounded-full font-semibold hover:bg-gray-700 transition shadow-lg"
              >
                Cancel
              </button>
            </div>
          </div>
          <canvas ref={canvasRef} className="hidden" />
        </div>
      )}

      {/* Preview Mode */}
      {mode === 'preview' && capturedImage && (
        <div className="space-y-4">
          <div className="border rounded-lg overflow-hidden">
            <img src={capturedImage} alt="Captured structure" className="w-full" />
          </div>
          <div className="flex gap-4">
            <button
              onClick={proceedToAnnotation}
              className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Next: Annotate →
            </button>
            <button
              onClick={retake}
              className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition"
            >
              Retake
            </button>
          </div>
        </div>
      )}

      {/* Annotate Mode */}
      {mode === 'annotate' && capturedImage && (
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">📍 Mark ArUco Marker Location</h3>
            <p className="text-sm text-blue-700">
              Click on the image where the ArUco marker is located, or skip if auto-detection should be used.
            </p>
          </div>
          
          <div className="border rounded-lg overflow-hidden relative cursor-crosshair">
            <img
              ref={imagePreviewRef}
              src={capturedImage}
              alt="Annotate structure"
              className="w-full hidden"
              onLoad={() => {
                // Trigger canvas redraw
                if (annotateCanvasRef.current && imagePreviewRef.current) {
                  const canvas = annotateCanvasRef.current
                  const img = imagePreviewRef.current
                  canvas.width = img.naturalWidth
                  canvas.height = img.naturalHeight
                  const ctx = canvas.getContext('2d')
                  if (ctx) {
                    ctx.drawImage(img, 0, 0)
                  }
                }
              }}
            />
            <canvas
              ref={annotateCanvasRef}
              onClick={handleCanvasClick}
              className="w-full"
            />
          </div>

          {markerPosition && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-700">
                ✓ Marker position set at ({Math.round(markerPosition.x)}, {Math.round(markerPosition.y)})
              </p>
            </div>
          )}

          <div className="bg-white border rounded-lg p-4">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Manual Scale (optional)
            </label>
            <input
              type="number"
              step="0.1"
              placeholder="e.g., 10 (feet)"
              value={manualScale}
              onChange={(e) => setManualScale(e.target.value)}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Enter a known dimension in feet if marker is not available
            </p>
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? '⏳ Analyzing...' : '🔍 Analyze Structure'}
            </button>
            <button
              onClick={retake}
              disabled={isAnalyzing}
              className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Marker Download Modal */}
      {showMarkerModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">ArUco Marker</h3>
              <button
                onClick={() => setShowMarkerModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Print this marker and place it near your structure for accurate scale detection.
              The marker should be clearly visible in your photo.
            </p>
            <div className="bg-gray-100 p-4 rounded text-center mb-4">
              <div className="inline-block bg-white p-4 border-2 border-black">
                {/* Placeholder for ArUco marker - in production would fetch from API */}
                <div className="w-48 h-48 bg-white border-4 border-black grid grid-cols-6 grid-rows-6">
                  {Array.from({ length: 36 }).map((_, i) => (
                    <div
                      key={i}
                      className={`${
                        [0, 1, 2, 3, 4, 5, 6, 11, 12, 17, 18, 23, 24, 29, 30, 31, 32, 33, 34, 35].includes(i)
                          ? 'bg-black'
                          : [14, 15, 20].includes(i)
                          ? 'bg-black'
                          : 'bg-white'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
            <button
              onClick={() => {
                // In production, would fetch from API and trigger download
                alert('Marker download functionality will fetch from GET /api/v1/marker')
                setShowMarkerModal(false)
              }}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Download Marker (PDF)
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
