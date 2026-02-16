import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const uploadImage = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  
  return response.data
}

export const getAnalysis = async (id: string) => {
  const response = await api.get(`/analysis/${id}`)
  return response.data
}

export const getHistory = async () => {
  const response = await api.get('/history')
  return response.data
}
