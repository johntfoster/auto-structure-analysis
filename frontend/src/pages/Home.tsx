import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="bg-white dark:bg-gray-900 transition-colors">
      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center min-h-[60vh] sm:min-h-[70vh] px-4 bg-gradient-to-b from-blue-50 to-white dark:from-gray-800 dark:to-gray-900">
        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-center mb-4 sm:mb-6 text-gray-900 dark:text-white">
          Snap. Analyze. Build with confidence.
        </h1>
        <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-gray-600 dark:text-gray-300 text-center mb-6 sm:mb-8 max-w-3xl px-4">
          Transform photos of truss structures into instant engineering analysis
          powered by computer vision and structural mechanics.
        </p>
        <Link
          to="/capture"
          className="bg-blue-600 dark:bg-blue-500 text-white px-8 sm:px-10 py-3 sm:py-4 rounded-lg text-lg sm:text-xl font-semibold hover:bg-blue-700 dark:hover:bg-blue-600 transition shadow-lg hover:shadow-xl touch-manipulation min-h-[44px]"
        >
          Get Started
        </Link>
      </div>

      {/* How It Works Section */}
      <div className="max-w-6xl mx-auto px-4 py-12 sm:py-16">
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-8 sm:mb-12 text-gray-900 dark:text-white">
          How It Works
        </h2>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6 sm:gap-8">
          {/* Step 1 */}
          <div className="text-center p-4 sm:p-6">
            <div className="w-12 h-12 sm:w-16 sm:h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
              <span className="text-2xl sm:text-3xl font-bold text-blue-600 dark:text-blue-400">1</span>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-gray-900 dark:text-white">
              Take Photo with Marker
            </h3>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Capture your truss structure with an ArUco marker for scale reference.
              Use your camera or upload an existing photo.
            </p>
          </div>

          {/* Step 2 */}
          <div className="text-center p-4 sm:p-6">
            <div className="w-12 h-12 sm:w-16 sm:h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
              <span className="text-2xl sm:text-3xl font-bold text-blue-600 dark:text-blue-400">2</span>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-gray-900 dark:text-white">
              AI Detects Structure
            </h3>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Our computer vision AI automatically identifies nodes, members,
              supports, and loads from your image.
            </p>
          </div>

          {/* Step 3 */}
          <div className="text-center p-4 sm:p-6">
            <div className="w-12 h-12 sm:w-16 sm:h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
              <span className="text-2xl sm:text-3xl font-bold text-blue-600 dark:text-blue-400">3</span>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-gray-900 dark:text-white">
              Get Instant Analysis
            </h3>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Receive detailed structural analysis including member forces,
              reactions, deflections, and safety factors.
            </p>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-gray-50 dark:bg-gray-800 py-12 sm:py-16">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-8 sm:mb-12 text-gray-900 dark:text-white">
            Features
          </h2>
          <div className="grid sm:grid-cols-2 gap-4 sm:gap-6 md:gap-8">
            <div className="bg-white dark:bg-gray-900 p-4 sm:p-6 rounded-lg shadow">
              <h3 className="text-lg sm:text-xl font-semibold mb-2 text-gray-900 dark:text-white">
                📐 Accurate Analysis
              </h3>
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
                Direct stiffness method for precise member forces, reactions, and deflections.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-900 p-4 sm:p-6 rounded-lg shadow">
              <h3 className="text-lg sm:text-xl font-semibold mb-2 text-gray-900 dark:text-white">
                🔄 What-If Scenarios
              </h3>
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
                Change materials, add loads, and reanalyze instantly without recapturing.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-900 p-4 sm:p-6 rounded-lg shadow">
              <h3 className="text-lg sm:text-xl font-semibold mb-2 text-gray-900 dark:text-white">
                📱 Mobile Friendly
              </h3>
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
                Capture and analyze structures anywhere with your phone or tablet.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-900 p-4 sm:p-6 rounded-lg shadow">
              <h3 className="text-lg sm:text-xl font-semibold mb-2 text-gray-900 dark:text-white">
                📊 Visual Results
              </h3>
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
                Color-coded force diagrams and comprehensive tables for easy understanding.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-12 sm:py-16 text-center">
        <h2 className="text-2xl sm:text-3xl font-bold mb-4 sm:mb-6 text-gray-900 dark:text-white">
          Ready to analyze your structure?
        </h2>
        <Link
          to="/capture"
          className="bg-blue-600 dark:bg-blue-500 text-white px-8 sm:px-10 py-3 sm:py-4 rounded-lg text-lg sm:text-xl font-semibold hover:bg-blue-700 dark:hover:bg-blue-600 transition shadow-lg hover:shadow-xl inline-block touch-manipulation min-h-[44px]"
        >
          Start Analyzing
        </Link>
      </div>
    </div>
  )
}
