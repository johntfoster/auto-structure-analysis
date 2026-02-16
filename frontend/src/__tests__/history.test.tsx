import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import History from '../pages/History'
import * as api from '../services/api'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const mockHistoryData: api.HistoryItem[] = [
  {
    id: 'test-1',
    thumbnail_url: 'http://example.com/thumb1.jpg',
    structure_type: 'Simple Truss',
    member_count: 5,
    created_at: '2024-01-01T12:00:00Z',
  },
  {
    id: 'test-2',
    thumbnail_url: 'http://example.com/thumb2.jpg',
    structure_type: 'Warren Truss',
    member_count: 8,
    created_at: '2024-01-02T14:30:00Z',
  },
]

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{component}</BrowserRouter>
    </QueryClientProvider>
  )
}

describe('History Page', () => {
  beforeEach(() => {
    queryClient.clear()
  })

  it('renders history page with mock data', async () => {
    vi.spyOn(api, 'getHistory').mockResolvedValue(mockHistoryData)

    renderWithRouter(<History />)

    await waitFor(() => {
      expect(screen.getByText(/Simple Truss/i)).toBeInTheDocument()
      expect(screen.getByText(/Warren Truss/i)).toBeInTheDocument()
    })
  })

  it('displays member count badges', async () => {
    vi.spyOn(api, 'getHistory').mockResolvedValue(mockHistoryData)

    renderWithRouter(<History />)

    await waitFor(() => {
      expect(screen.getByText(/5 members/i)).toBeInTheDocument()
      expect(screen.getByText(/8 members/i)).toBeInTheDocument()
    })
  })

  it('shows empty state when no history exists', async () => {
    vi.spyOn(api, 'getHistory').mockResolvedValue([])

    renderWithRouter(<History />)

    await waitFor(() => {
      expect(screen.getByText(/No analyses yet/i)).toBeInTheDocument()
      expect(screen.getByText(/Capture Your First Structure/i)).toBeInTheDocument()
    })
  })

  it('displays new analysis button', async () => {
    vi.spyOn(api, 'getHistory').mockResolvedValue(mockHistoryData)

    renderWithRouter(<History />)

    await waitFor(() => {
      expect(screen.getByText(/\+ New Analysis/i)).toBeInTheDocument()
    })
  })

  it('shows loading state initially', () => {
    vi.spyOn(api, 'getHistory').mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    renderWithRouter(<History />)

    expect(screen.getByText(/Loading history/i)).toBeInTheDocument()
  })
})
