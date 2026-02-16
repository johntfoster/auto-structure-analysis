import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from './contexts/ThemeContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import Capture from './pages/Capture'
import Analyze from './pages/Analyze'
import History from './pages/History'
import Marker from './pages/Marker'
import Settings from './pages/Settings'
import InstallPrompt from './components/InstallPrompt'

const queryClient = new QueryClient()

function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Home />} />
              <Route path="capture" element={<Capture />} />
              <Route path="analyze/:id" element={<Analyze />} />
              <Route path="history" element={<History />} />
              <Route path="marker" element={<Marker />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
          <InstallPrompt />
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

export default App
