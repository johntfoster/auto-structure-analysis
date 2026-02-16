import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api, analyzeImage, getAnalysis, reanalyze, getHistory, getMarker } from '../services/api'
import type { AnalysisResult, HistoryItem } from '../services/api'

// Mock axios
vi.mock('axios', () => {
  return {
    default: {
      create: vi.fn(() => ({
        get: vi.fn(),
        post: vi.fn(),
        defaults: {
          baseURL: 'http://localhost:8000/api/v1',
          headers: {
            'Content-Type': 'application/json',
          },
        },
      })),
    },
  }
})

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates axios instance with correct base URL', () => {
    expect(api.defaults.baseURL).toContain('/api/v1')
  })

  it('has correct default headers', () => {
    expect(api.defaults.headers['Content-Type']).toBe('application/json')
  })

  describe('analyzeImage', () => {
    it('sends multipart form data with image file', async () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      const mockResponse: AnalysisResult = {
        id: 'test-123',
        image_url: 'http://example.com/image.jpg',
        structure_type: 'Simple Truss',
        member_count: 5,
        node_count: 4,
        members: [],
        nodes: [],
        loads: [],
        max_deflection: 0.25,
        safety_status: 'pass',
        created_at: '2024-01-01T12:00:00Z',
      }

      api.post = vi.fn().mockResolvedValue({ data: mockResponse })

      const result = await analyzeImage({ image: mockFile })

      expect(api.post).toHaveBeenCalledWith(
        '/analyze',
        expect.any(FormData),
        expect.objectContaining({
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('includes marker position when provided', async () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      const mockResponse: AnalysisResult = {
        id: 'test-123',
        image_url: 'http://example.com/image.jpg',
        structure_type: 'Simple Truss',
        member_count: 5,
        node_count: 4,
        members: [],
        nodes: [],
        loads: [],
        max_deflection: 0.25,
        safety_status: 'pass',
        created_at: '2024-01-01T12:00:00Z',
      }

      api.post = vi.fn().mockResolvedValue({ data: mockResponse })

      await analyzeImage({
        image: mockFile,
        marker_position: { x: 100, y: 200 },
      })

      expect(api.post).toHaveBeenCalled()
      const formData = (api.post as any).mock.calls[0][1] as FormData
      expect(formData.get('marker_x')).toBe('100')
      expect(formData.get('marker_y')).toBe('200')
    })
  })

  describe('getAnalysis', () => {
    it('fetches analysis by id', async () => {
      const mockResponse: AnalysisResult = {
        id: 'test-123',
        image_url: 'http://example.com/image.jpg',
        structure_type: 'Simple Truss',
        member_count: 5,
        node_count: 4,
        members: [],
        nodes: [],
        loads: [],
        max_deflection: 0.25,
        safety_status: 'pass',
        created_at: '2024-01-01T12:00:00Z',
      }

      api.get = vi.fn().mockResolvedValue({ data: mockResponse })

      const result = await getAnalysis('test-123')

      expect(api.get).toHaveBeenCalledWith('/analysis/test-123')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('reanalyze', () => {
    it('sends reanalysis request with updates', async () => {
      const mockResponse: AnalysisResult = {
        id: 'test-123',
        image_url: 'http://example.com/image.jpg',
        structure_type: 'Simple Truss',
        member_count: 5,
        node_count: 4,
        members: [],
        nodes: [],
        loads: [],
        max_deflection: 0.25,
        safety_status: 'pass',
        created_at: '2024-01-01T12:00:00Z',
      }

      api.post = vi.fn().mockResolvedValue({ data: mockResponse })

      const updates = {
        material: 'aluminum',
        loads: [{ node_id: 1, fx: 10, fy: 0 }],
      }

      const result = await reanalyze('test-123', updates)

      expect(api.post).toHaveBeenCalledWith('/analysis/test-123/reanalyze', updates)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getHistory', () => {
    it('fetches analysis history', async () => {
      const mockResponse: HistoryItem[] = [
        {
          id: 'test-1',
          thumbnail_url: 'http://example.com/thumb1.jpg',
          structure_type: 'Simple Truss',
          member_count: 5,
          created_at: '2024-01-01T12:00:00Z',
        },
      ]

      api.get = vi.fn().mockResolvedValue({ data: mockResponse })

      const result = await getHistory()

      expect(api.get).toHaveBeenCalledWith('/analyses')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getMarker', () => {
    it('fetches marker as blob', async () => {
      const mockBlob = new Blob(['marker'], { type: 'image/png' })

      api.get = vi.fn().mockResolvedValue({ data: mockBlob })

      const result = await getMarker()

      expect(api.get).toHaveBeenCalledWith('/marker', {
        responseType: 'blob',
      })
      expect(result).toEqual(mockBlob)
    })
  })
})
