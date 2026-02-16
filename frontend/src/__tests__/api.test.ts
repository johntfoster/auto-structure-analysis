import { describe, it, expect } from 'vitest'
import { api } from '../services/api'

describe('API Service', () => {
  it('creates axios instance with correct base URL', () => {
    expect(api.defaults.baseURL).toBe('http://localhost:8000/api/v1')
  })

  it('has correct default headers', () => {
    expect(api.defaults.headers['Content-Type']).toBe('application/json')
  })
})
