import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Analyze from '../pages/Analyze'
import * as api from '../services/api'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const mockAnalysisData: api.AnalysisResult = {
  id: 'test-123',
  image_url: 'http://example.com/image.jpg',
  structure_type: 'Simple Truss',
  member_count: 5,
  node_count: 4,
  members: [
    { id: 1, start_node: 1, end_node: 2, axial_force: 10.5, stress_ratio: 0.3 },
    { id: 2, start_node: 2, end_node: 3, axial_force: -8.2, stress_ratio: 0.25 },
    { id: 3, start_node: 3, end_node: 4, axial_force: 0.0, stress_ratio: 0.0 },
  ],
  nodes: [
    { id: 1, x: 0, y: 0, support_type: 'pin', reaction_x: 5.0, reaction_y: 10.0 },
    { id: 2, x: 10, y: 0, support_type: null },
    { id: 3, x: 20, y: 0, support_type: null },
    { id: 4, x: 30, y: 0, support_type: 'roller', reaction_x: 0, reaction_y: 8.0 },
  ],
  loads: [
    { node_id: 2, fx: 0, fy: -5 },
  ],
  max_deflection: 0.25,
  safety_status: 'pass',
  created_at: '2024-01-01T12:00:00Z',
}

const renderWithRouter = (component: React.ReactElement, route = '/analyze/test-123') => {
  window.history.pushState({}, 'Test page', route)
  
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/analyze/:id" element={component} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Analysis Visualization', () => {
  beforeEach(() => {
    // Mock canvas context
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
      clearRect: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      arc: vi.fn(),
      fill: vi.fn(),
      fillText: vi.fn(),
      closePath: vi.fn(),
      strokeStyle: '',
      fillStyle: '',
      lineWidth: 0,
      font: '',
      textAlign: '',
    })

    // Mock API
    vi.spyOn(api, 'getAnalysis').mockResolvedValue(mockAnalysisData)
  })

  it('renders analysis visualization with mock data', async () => {
    renderWithRouter(<Analyze />)

    await waitFor(() => {
      expect(screen.getByText(/Analysis Results/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/Simple Truss/i)).toBeInTheDocument()
    expect(screen.getByText(/5 members/i)).toBeInTheDocument()
  })

  it('displays member forces table', async () => {
    renderWithRouter(<Analyze />)

    await waitFor(() => {
      expect(screen.getByText(/Member Forces/i)).toBeInTheDocument()
    })

    // Check for tension member
    expect(screen.getByText(/Tension/i)).toBeInTheDocument()
    // Check for compression member
    expect(screen.getByText(/Compression/i)).toBeInTheDocument()
  })

  it('displays reactions table', async () => {
    renderWithRouter(<Analyze />)

    await waitFor(() => {
      expect(screen.getByText(/Reactions/i)).toBeInTheDocument()
    })
  })

  it('displays safety summary', async () => {
    renderWithRouter(<Analyze />)

    await waitFor(() => {
      expect(screen.getByText(/Safety Summary/i)).toBeInTheDocument()
      expect(screen.getByText(/PASS/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/Max Deflection/i)).toBeInTheDocument()
  })

  it('displays what-if controls', async () => {
    renderWithRouter(<Analyze />)

    await waitFor(() => {
      expect(screen.getByText(/What-If Analysis/i)).toBeInTheDocument()
    })

    // Check for material selector
    const materialSelect = screen.getByRole('combobox')
    expect(materialSelect).toBeInTheDocument()
  })

  it('has export button', async () => {
    renderWithRouter(<Analyze />)

    await waitFor(() => {
      expect(screen.getByText(/Export JSON/i)).toBeInTheDocument()
    })
  })
})
