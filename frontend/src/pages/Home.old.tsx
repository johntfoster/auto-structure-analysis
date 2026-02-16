import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="bg-white">
      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 bg-gradient-to-b from-blue-50 to-white">
        <h1 className="text-5xl md:text-6xl font-bold text-center mb-6 text-gray-900">
          Snap. Analyze. Build with confidence.
        </h1>
        <p className="text-xl md:text-2xl text-gray-600 text-center mb-8 max-w-3xl">
          Transform photos of truss structures into instant engineering analysis
          powered by computer vision and structural mechanics.
        </p>
        <Link
          to="/capture"
          className="bg-blue-600 text-white px-10 py-4 rounded-lg text-xl font-semibold hover:bg-blue-700 transition shadow-lg hover:shadow-xl"
        >
          Get Started
        </Link>
      </div>

      {/* How It Works Section */}
      <div className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-4xl font-bold text-center mb-12 text-gray-900">
          How It Works
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {/* Step 1 */}
          <div className="text-center p-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl font-bold text-blue-600">1</span>
            </div>
            <h3 className="text-xl font-semibold mb-3 text-gray-900">
              Take Photo with Marker
            </h3>
            <p className="text-gray-600">
              Capture your truss structure with an ArUco marker for scale reference.
              Use your camera or upload an existing photo.
            </p>
          </div>

          {/* Step 2 */}
          <div className="text-center p-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl font-bold text-blue-600">2</span>
            </div>
            <h3 className="text-xl font-semibold mb-3 text-gray-900">
              AI Detects Structure
            </h3>
            <p className="text-gray-600">
              Our computer vision AI automatically identifies nodes, members,
              supports, and loads from your image.
            </p>
          </div>

          {/* Step 3 */}
          <div className="text-center p-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl font-bold text-blue-600">3</span>
            </div>
            <h3 className="text-xl font-semibold mb-3 text-gray-900">
              Get Instant Analysis
            </h3>
            <p className="text-gray-600">
              Receive detailed structural analysis including member forces,
              reactions, deflections, and safety factors.
            </p>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
            Features
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-xl font-semibold mb-2 text-gray-900">
                📐 Accurate Analysis
              </h3>
              <p className="text-gray-600">
                Direct stiffness method for precise member forces, reactions, and deflections.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-xl font-semibold mb-2 text-gray-900">
                🔄 What-If Scenarios
              </h3>
              <p className="text-gray-600">
                Change materials, add loads, and reanalyze instantly without recapturing.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-xl font-semibold mb-2 text-gray-900">
                📱 Mobile Friendly
              </h3>
              <p className="text-gray-600">
                Capture and analyze structures anywhere with your phone or tablet.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-xl font-semibold mb-2 text-gray-900">
                📊 Visual Results
              </h3>
              <p className="text-gray-600">
                Color-coded force diagrams and comprehensive tables for easy understanding.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 text-center">
        <h2 className="text-3xl font-bold mb-6 text-gray-900">
          Ready to analyze your structure?
        </h2>
        <Link
          to="/capture"
          className="bg-blue-600 text-white px-10 py-4 rounded-lg text-xl font-semibold hover:bg-blue-700 transition shadow-lg hover:shadow-xl inline-block"
        >
          Start Analyzing
        </Link>
      </div>
    </div>
  )
}
