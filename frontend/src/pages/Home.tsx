import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
      <h1 className="text-5xl font-bold text-center mb-6">
        Analyze Structures from Photos
      </h1>
      <p className="text-xl text-gray-600 text-center mb-8 max-w-2xl">
        Upload a photo of a truss structure and get instant structural analysis
        powered by AI and engineering principles.
      </p>
      <Link
        to="/capture"
        className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 transition"
      >
        Get Started
      </Link>
    </div>
  )
}
