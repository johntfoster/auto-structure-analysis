import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'
import { Capacitor } from '@capacitor/core'

export interface CameraOptions {
  quality?: number
  allowEditing?: boolean
  resultType?: CameraResultType
  source?: CameraSource
}

export interface CameraPhoto {
  dataUrl: string
  file: File
}

/**
 * Camera service with Capacitor Camera API and web fallback
 */
export class CameraService {
  /**
   * Check if running on a native platform
   */
  static isNative(): boolean {
    return Capacitor.isNativePlatform()
  }

  /**
   * Take a photo using Capacitor Camera API (native) or web fallback
   */
  static async takePhoto(options: CameraOptions = {}): Promise<CameraPhoto> {
    const {
      quality = 90,
      allowEditing = false,
      resultType = CameraResultType.DataUrl,
      source = CameraSource.Camera,
    } = options

    if (this.isNative()) {
      // Use Capacitor Camera API on native platforms
      const photo = await Camera.getPhoto({
        quality,
        allowEditing,
        resultType,
        source,
      })

      // Convert to File
      const response = await fetch(photo.dataUrl!)
      const blob = await response.blob()
      const file = new File([blob], `capture-${Date.now()}.jpg`, { type: 'image/jpeg' })

      return {
        dataUrl: photo.dataUrl!,
        file,
      }
    } else {
      // Web fallback using HTML5 getUserMedia
      return this.takePhotoWeb()
    }
  }

  /**
   * Pick photo from gallery
   */
  static async pickPhoto(options: CameraOptions = {}): Promise<CameraPhoto> {
    const {
      quality = 90,
      allowEditing = false,
      resultType = CameraResultType.DataUrl,
    } = options

    if (this.isNative()) {
      const photo = await Camera.getPhoto({
        quality,
        allowEditing,
        resultType,
        source: CameraSource.Photos,
      })

      const response = await fetch(photo.dataUrl!)
      const blob = await response.blob()
      const file = new File([blob], `upload-${Date.now()}.jpg`, { type: 'image/jpeg' })

      return {
        dataUrl: photo.dataUrl!,
        file,
      }
    } else {
      // Web fallback - file input
      return this.pickPhotoWeb()
    }
  }

  /**
   * Web fallback for taking photo (returns a promise that can be used with a video element)
   */
  private static async takePhotoWeb(): Promise<CameraPhoto> {
    return new Promise((resolve, reject) => {
      // Create video element
      const video = document.createElement('video')
      video.setAttribute('autoplay', '')
      video.setAttribute('playsinline', '')

      // Create canvas for capture
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')

      // Request camera access
      navigator.mediaDevices
        .getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
          audio: false,
        })
        .then((stream) => {
          video.srcObject = stream

          // Wait for video to be ready
          video.onloadedmetadata = () => {
            // Setup canvas
            canvas.width = video.videoWidth
            canvas.height = video.videoHeight

            // Draw and capture (we need to expose a way to trigger this)
            // For now, auto-capture after a delay (in real use, you'd have a button)
            setTimeout(() => {
              if (context) {
                context.drawImage(video, 0, 0, canvas.width, canvas.height)

                canvas.toBlob(
                  (blob) => {
                    if (blob) {
                      const file = new File([blob], `capture-${Date.now()}.jpg`, {
                        type: 'image/jpeg',
                      })
                      const dataUrl = canvas.toDataURL('image/jpeg', 0.9)

                      // Stop stream
                      stream.getTracks().forEach((track) => track.stop())

                      resolve({ dataUrl, file })
                    } else {
                      reject(new Error('Failed to create blob from canvas'))
                    }
                  },
                  'image/jpeg',
                  0.9
                )
              }
            }, 100)
          }
        })
        .catch((error) => {
          reject(error)
        })
    })
  }

  /**
   * Web fallback for picking photo from file system
   */
  private static async pickPhotoWeb(): Promise<CameraPhoto> {
    return new Promise((resolve, reject) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = 'image/*'

      input.onchange = (e) => {
        const file = (e.target as HTMLInputElement).files?.[0]
        if (file) {
          const reader = new FileReader()
          reader.onload = (event) => {
            resolve({
              dataUrl: event.target?.result as string,
              file,
            })
          }
          reader.onerror = () => reject(new Error('Failed to read file'))
          reader.readAsDataURL(file)
        } else {
          reject(new Error('No file selected'))
        }
      }

      input.click()
    })
  }

  /**
   * Check camera permissions
   */
  static async checkPermissions(): Promise<boolean> {
    if (this.isNative()) {
      const permissions = await Camera.checkPermissions()
      return permissions.camera === 'granted'
    } else {
      // Web - check if getUserMedia is available
      return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
    }
  }

  /**
   * Request camera permissions
   */
  static async requestPermissions(): Promise<boolean> {
    if (this.isNative()) {
      const permissions = await Camera.requestPermissions()
      return permissions.camera === 'granted'
    } else {
      // Web - permissions are requested when getUserMedia is called
      return true
    }
  }
}
