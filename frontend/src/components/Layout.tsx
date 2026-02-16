import { Link, Outlet, useLocation } from 'react-router-dom'

export default function Layout() {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-gray-900 shadow-lg">
        <nav className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <span className="text-2xl">📐</span>
              <span className="text-2xl font-bold text-white">
                Auto Structure
              </span>
            </Link>
            <div className="flex gap-6">
              <Link
                to="/"
                className={`transition font-medium ${
                  isActive('/')
                    ? 'text-blue-400'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Home
              </Link>
              <Link
                to="/capture"
                className={`transition font-medium ${
                  isActive('/capture')
                    ? 'text-blue-400'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Capture
              </Link>
              <Link
                to="/history"
                className={`transition font-medium ${
                  isActive('/history')
                    ? 'text-blue-400'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                History
              </Link>
              <Link
                to="/settings"
                className={`transition font-medium ${
                  isActive('/settings')
                    ? 'text-blue-400'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Settings
              </Link>
            </div>
          </div>
        </nav>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="bg-gray-900 text-gray-400 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm">
          <p>Auto Structure Analysis • Powered by Computer Vision & Structural Mechanics</p>
        </div>
      </footer>
    </div>
  )
}
