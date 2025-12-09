'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import FaceCapture from '@/components/auth/FaceCapture'
import { authApi } from '@/lib/api/auth'
import { toast } from 'sonner'
import { LogIn, Mail } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [useFallback, setUseFallback] = useState(false)
  
  const [fallbackData, setFallbackData] = useState({
    email: '',
    password: '',
  })

  const handleFaceLogin = async (base64Image: string) => {
    setLoading(true)

    try {
      await authApi.login({
        face_image_base64: base64Image,
      })

      toast.success('Welcome back! Ì±ã')
      router.push('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Face login failed. Try email/password.')
      setUseFallback(true)
    } finally {
      setLoading(false)
    }
  }

  const handleFallbackLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      await authApi.login({
        face_image_base64: '',
        email: fallbackData.email,
        password: fallbackData.password,
      })

      toast.success('Welcome back! Ì±ã')
      router.push('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <LogIn className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Welcome Back</h1>
          <p className="text-gray-600 mt-2">
            {!useFallback ? 'Login with your face Ì≥∏' : 'Login with email Ì≥ß'}
          </p>
        </div>

        {!useFallback ? (
          <div>
            <FaceCapture onCapture={handleFaceLogin} />
            
            <div className="mt-6 space-y-3">
              <button
                onClick={() => setUseFallback(true)}
                className="w-full py-2 text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center justify-center gap-2"
              >
                <Mail className="w-4 h-4" />
                Use email & password instead
              </button>
            </div>

            {loading && (
              <div className="text-center mt-4">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
                <p className="text-sm text-gray-600 mt-2">Verifying your face...</p>
              </div>
            )}
          </div>
        ) : (
          <form onSubmit={handleFallbackLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                required
                value={fallbackData.email}
                onChange={(e) => setFallbackData({ ...fallbackData, email: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={fallbackData.password}
                onChange={(e) => setFallbackData({ ...fallbackData, password: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="Your password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition disabled:bg-gray-400"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>

            <button
              type="button"
              onClick={() => setUseFallback(false)}
              className="w-full py-2 text-sm text-gray-600 hover:text-gray-700"
            >
              ‚Üê Back to face login
            </button>
          </form>
        )}

        <p className="text-center text-sm text-gray-600 mt-6">
          Don't have an account?{' '}
          <a href="/register" className="text-blue-600 hover:underline font-medium">
            Register
          </a>
        </p>
      </div>
    </div>
  )
}
