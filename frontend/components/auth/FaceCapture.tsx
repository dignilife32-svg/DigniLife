'use client'

import { useRef, useState, useCallback } from 'react'
import Webcam from 'react-webcam'
import { Camera, CheckCircle, XCircle } from 'lucide-react'

interface FaceCaptureProps {
  onCapture: (base64Image: string) => void
  onCancel?: () => void
}

export default function FaceCapture({ onCapture, onCancel }: FaceCaptureProps) {
  const webcamRef = useRef<Webcam>(null)
  const [captured, setCaptured] = useState(false)
  const [capturedImage, setCapturedImage] = useState<string | null>(null)

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot()
    if (imageSrc) {
      setCapturedImage(imageSrc)
      setCaptured(true)
    }
  }, [webcamRef])

  const retake = () => {
    setCaptured(false)
    setCapturedImage(null)
  }

  const confirm = () => {
    if (capturedImage) {
      const base64 = capturedImage.split(',')[1]
      onCapture(base64)
    }
  }

  return (
    <div className="flex flex-col items-center space-y-4">
      <div className="relative w-full max-w-md aspect-video bg-gray-900 rounded-lg overflow-hidden">
        {!captured ? (
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            videoConstraints={{
              width: 640,
              height: 480,
              facingMode: "user"
            }}
            className="w-full h-full object-cover"
          />
        ) : (
          capturedImage && (
            <img 
              src={capturedImage} 
              alt="Captured face" 
              className="w-full h-full object-cover"
            />
          )
        )}

        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-64 h-80 border-4 border-white/50 rounded-full"></div>
        </div>
      </div>

      <div className="text-center">
        <p className="text-sm text-gray-600">
          {!captured 
            ? "Position your face within the circle" 
            : "Does this photo look good?"
          }
        </p>
      </div>

      <div className="flex gap-3">
        {!captured ? (
          <>
            <button
              onClick={capture}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              <Camera className="w-5 h-5" />
              Capture Photo
            </button>
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
              >
                Cancel
              </button>
            )}
          </>
        ) : (
          <>
            <button
              onClick={confirm}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
            >
              <CheckCircle className="w-5 h-5" />
              Use This Photo
            </button>
            <button
              onClick={retake}
              className="flex items-center gap-2 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
            >
              <XCircle className="w-5 h-5" />
              Retake
            </button>
          </>
        )}
      </div>
    </div>
  )
}
