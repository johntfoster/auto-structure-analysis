import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Marker from '../pages/Marker'
import * as api from '../services/api'

vi.mock('../services/api')

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
})

function renderMarkerPage() {
  return render(
    <QueryClientProvider client={queryClient}>
      <Marker />
    </QueryClientProvider>
  )
}

describe('Marker Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    vi.mocked(api.getMarker).mockImplementation(() => new Promise(() => {}))
    renderMarkerPage()
    
    expect(screen.getByText(/loading marker/i)).toBeInTheDocument()
  })

  it('loads and displays marker', async () => {
    const mockBlob = new Blob(['fake-image-data'], { type: 'image/png' })
    vi.mocked(api.getMarker).mockResolvedValue(mockBlob)

    renderMarkerPage()

    await waitFor(() => {
      expect(screen.getByAltText(/aruco marker/i)).toBeInTheDocument()
    })
  })

  it('displays error when marker fails to load', async () => {
    vi.mocked(api.getMarker).mockRejectedValue(new Error('Network error'))

    renderMarkerPage()

    await waitFor(() => {
      expect(screen.getByText(/failed to load aruco marker/i)).toBeInTheDocument()
    })
  })

  it('shows usage instructions', async () => {
    const mockBlob = new Blob(['fake-image-data'], { type: 'image/png' })
    vi.mocked(api.getMarker).mockResolvedValue(mockBlob)

    renderMarkerPage()

    await waitFor(() => {
      expect(screen.getByText(/how to use this marker/i)).toBeInTheDocument()
    })
  })

  it('provides print and download buttons', async () => {
    const mockBlob = new Blob(['fake-image-data'], { type: 'image/png' })
    vi.mocked(api.getMarker).mockResolvedValue(mockBlob)

    renderMarkerPage()

    await waitFor(() => {
      expect(screen.getByText(/print marker/i)).toBeInTheDocument()
      expect(screen.getByText(/download png/i)).toBeInTheDocument()
    })
  })
})
