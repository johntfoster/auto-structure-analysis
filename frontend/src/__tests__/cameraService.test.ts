import { describe, it, expect, vi, beforeEach } from 'vitest'
import { CameraService } from '../services/camera'
import { Capacitor } from '@capacitor/core'
import { Camera } from '@capacitor/camera'

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(),
  },
}))

vi.mock('@capacitor/camera', () => ({
  Camera: {
    getPhoto: vi.fn(),
    checkPermissions: vi.fn(),
    requestPermissions: vi.fn(),
  },
  CameraResultType: {
    DataUrl: 'dataUrl',
    Uri: 'uri',
    Base64: 'base64',
  },
  CameraSource: {
    Camera: 'camera',
    Photos: 'photos',
    Prompt: 'prompt',
  },
}))

describe('CameraService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('isNative', () => {
    it('returns true on native platform', () => {
      vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true)
      expect(CameraService.isNative()).toBe(true)
    })

    it('returns false on web platform', () => {
      vi.mocked(Capacitor.isNativePlatform).mockReturnValue(false)
      expect(CameraService.isNative()).toBe(false)
    })
  })

  describe('checkPermissions', () => {
    it('checks native camera permissions when on native platform', async () => {
      vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true)
      vi.mocked(Camera.checkPermissions).mockResolvedValue({ camera: 'granted', photos: 'granted' })

      const result = await CameraService.checkPermissions()
      expect(result).toBe(true)
      expect(Camera.checkPermissions).toHaveBeenCalled()
    })

    it('returns false when native permissions denied', async () => {
      vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true)
      vi.mocked(Camera.checkPermissions).mockResolvedValue({ camera: 'denied', photos: 'denied' })

      const result = await CameraService.checkPermissions()
      expect(result).toBe(false)
    })

    it('checks getUserMedia availability on web', async () => {
      vi.mocked(Capacitor.isNativePlatform).mockReturnValue(false)
      
      // Mock getUserMedia
      Object.defineProperty(navigator, 'mediaDevices', {
        writable: true,
        value: {
          getUserMedia: vi.fn(),
        },
      })

      const result = await CameraService.checkPermissions()
      expect(result).toBe(true)
    })
  })

  describe('requestPermissions', () => {
    it('requests native camera permissions when on native platform', async () => {
      vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true)
      vi.mocked(Camera.requestPermissions).mockResolvedValue({ camera: 'granted', photos: 'granted' })

      const result = await CameraService.requestPermissions()
      expect(result).toBe(true)
      expect(Camera.requestPermissions).toHaveBeenCalled()
    })

    it('returns true on web (permissions requested on getUserMedia call)', async () => {
      vi.mocked(Capacitor.isNativePlatform).mockReturnValue(false)

      const result = await CameraService.requestPermissions()
      expect(result).toBe(true)
    })
  })

  describe('takePhoto - native', () => {
    it('uses Capacitor Camera API on native platform', async () => {
      vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true)
      
      const mockDataUrl = 'data:image/jpeg;base64,mockimage'
      vi.mocked(Camera.getPhoto).mockResolvedValue({
        dataUrl: mockDataUrl,
        format: 'jpeg',
        saved: false,
      })

      // Mock fetch for converting dataUrl to blob
      globalThis.fetch = vi.fn().mockResolvedValue({
        blob: () => Promise.resolve(new Blob(['mock'], { type: 'image/jpeg' })),
      })

      const result = await CameraService.takePhoto()
      
      expect(Camera.getPhoto).toHaveBeenCalledWith({
        quality: 90,
        allowEditing: false,
        resultType: 'dataUrl',
        source: 'camera',
      })
      expect(result.dataUrl).toBe(mockDataUrl)
      expect(result.file).toBeInstanceOf(File)
      expect(result.file.type).toBe('image/jpeg')
    })
  })

  describe('pickPhoto - native', () => {
    it('uses Capacitor Camera API with Photos source', async () => {
      vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true)
      
      const mockDataUrl = 'data:image/jpeg;base64,mockimage'
      vi.mocked(Camera.getPhoto).mockResolvedValue({
        dataUrl: mockDataUrl,
        format: 'jpeg',
        saved: false,
      })

      globalThis.fetch = vi.fn().mockResolvedValue({
        blob: () => Promise.resolve(new Blob(['mock'], { type: 'image/jpeg' })),
      })

      const result = await CameraService.pickPhoto()
      
      expect(Camera.getPhoto).toHaveBeenCalledWith({
        quality: 90,
        allowEditing: false,
        resultType: 'dataUrl',
        source: 'photos',
      })
      expect(result.dataUrl).toBe(mockDataUrl)
      expect(result.file).toBeInstanceOf(File)
    })
  })
})
