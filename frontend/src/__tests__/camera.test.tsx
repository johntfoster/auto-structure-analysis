import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '../contexts/ThemeContext'
import Capture from '../pages/Capture'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>{component}</BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

describe('Camera Component', () => {
  beforeEach(() => {
    // Mock getUserMedia
    Object.defineProperty(window.navigator, 'mediaDevices', {
      writable: true,
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockResolvedValue({
          getTracks: () => [
            {
              stop: vi.fn(),
            },
          ],
        }),
      },
    })

    // Mock canvas
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
      drawImage: vi.fn(),
      clearRect: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      arc: vi.fn(),
      fill: vi.fn(),
      fillText: vi.fn(),
      strokeStyle: '',
      fillStyle: '',
      lineWidth: 0,
      font: '',
      textAlign: '',
    })

    HTMLCanvasElement.prototype.toBlob = vi.fn((callback) => {
      const blob = new Blob(['fake'], { type: 'image/jpeg' })
      callback(blob)
    })

    HTMLCanvasElement.prototype.toDataURL = vi.fn(() => 'data:image/jpeg;base64,fake')
  })

  it('renders camera component', () => {
    renderWithRouter(<Capture />)
    expect(screen.getByText(/Capture Structure/i)).toBeInTheDocument()
  })

  it('starts camera when button is clicked', async () => {
    renderWithRouter(<Capture />)
    const button = screen.getByText(/Open Camera/i)
    fireEvent.click(button)

    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
      video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
      audio: false,
    })
  })

  it('handles camera permission error gracefully', async () => {
    const mockGetUserMedia = vi.fn().mockRejectedValue(new Error('Permission denied'))
    Object.defineProperty(window.navigator, 'mediaDevices', {
      writable: true,
      value: {
        getUserMedia: mockGetUserMedia,
      },
    })

    renderWithRouter(<Capture />)
    const button = screen.getByText(/Open Camera/i)
    fireEvent.click(button)

    // Error should be handled without crashing
    expect(mockGetUserMedia).toHaveBeenCalled()
  })

  it('shows marker print link', () => {
    renderWithRouter(<Capture />)
    const link = screen.getByText(/Print ArUco Marker/i)
    expect(link).toBeInTheDocument()
  })
})
