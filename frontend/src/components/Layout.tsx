import { Link, Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white shadow">
        <nav className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="text-2xl font-bold text-blue-600">
              Auto Structure
            </Link>
            <div className="flex gap-6">
              <Link
                to="/"
                className="text-gray-700 hover:text-blue-600 transition"
              >
                Home
              </Link>
              <Link
                to="/capture"
                className="text-gray-700 hover:text-blue-600 transition"
              >
                Capture
              </Link>
              <Link
                to="/history"
                className="text-gray-700 hover:text-blue-600 transition"
              >
                History
              </Link>
              <Link
                to="/settings"
                className="text-gray-700 hover:text-blue-600 transition"
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
    </div>
  )
}
