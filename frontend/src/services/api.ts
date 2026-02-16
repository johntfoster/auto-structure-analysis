import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface AnalysisRequest {
  image: File
  marker_position?: { x: number; y: number }
  manual_scale?: number
  material?: string
  loads?: Array<{ node_id: number; fx: number; fy: number }>
}

export interface Member {
  id: number
  start_node: number
  end_node: number
  axial_force: number
  stress_ratio: number
}

export interface Node {
  id: number
  x: number
  y: number
  support_type?: 'pin' | 'roller' | null
  reaction_x?: number
  reaction_y?: number
}

export interface Load {
  node_id: number
  fx: number
  fy: number
}

export interface AnalysisResult {
  id: string
  image_url: string
  structure_type: string
  member_count: number
  node_count: number
  members: Member[]
  nodes: Node[]
  loads: Load[]
  max_deflection: number
  safety_status: 'pass' | 'fail'
  created_at: string
}

export interface HistoryItem {
  id: string
  thumbnail_url: string
  structure_type: string
  member_count: number
  created_at: string
}

export const analyzeImage = async (data: AnalysisRequest): Promise<AnalysisResult> => {
  const formData = new FormData()
  formData.append('file', data.image)
  
  if (data.marker_position) {
    formData.append('marker_x', data.marker_position.x.toString())
    formData.append('marker_y', data.marker_position.y.toString())
  }
  
  if (data.manual_scale) {
    formData.append('manual_scale', data.manual_scale.toString())
  }
  
  if (data.material) {
    formData.append('material', data.material)
  }
  
  if (data.loads) {
    formData.append('loads', JSON.stringify(data.loads))
  }
  
  const response = await api.post<AnalysisResult>('/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  
  return response.data
}

export const getAnalysis = async (id: string): Promise<AnalysisResult> => {
  const response = await api.get<AnalysisResult>(`/analysis/${id}`)
  return response.data
}

export const reanalyze = async (
  id: string,
  updates: { material?: string; loads?: Array<{ node_id: number; fx: number; fy: number }> }
): Promise<AnalysisResult> => {
  const response = await api.post<AnalysisResult>(`/analysis/${id}/reanalyze`, updates)
  return response.data
}

export const getHistory = async (): Promise<HistoryItem[]> => {
  const response = await api.get<HistoryItem[]>('/analyses')
  return response.data
}

export const getMarker = async (): Promise<Blob> => {
  const response = await api.get('/marker', {
    responseType: 'blob',
  })
  return response.data
}
