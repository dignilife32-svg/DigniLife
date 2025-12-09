'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import FaceCapture from '@/components/auth/FaceCapture'
import { authApi } from '@/lib/api/auth'
import { toast } from 'sonner'

export default function RegisterPage() {
  const router = useRouter()
  const [step, setStep] = useState<1 | 2>(1)
  const [loading, setLoading] = useState(false)
  
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    phone_number: '',
    password: '',
  })

  const handleNextStep = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.email || !formData.full_name) {
      toast.error('Please fill in required fields')
      return
    }
    
    setStep(2)
  }

  const handleFaceCapture = async (base64Image: string) => {
    setLoading(true)

    try {
      await authApi.register({
        ...formData,
        password: formData.password || undefined,
        face_image_base64: base64Image,
      })

      toast.success('Account created successfully! í¾‰')
      
      await authApi.login({
        face_image_base64: base64Image,
        email: formData.email,
      })

      router.push('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
      setStep(1)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Join DigniLife</h1>
          <p className="text-gray-600 mt-2">
            {step === 1 ? 'Create your account' : 'Verify your face'}
          </p>
        </div>

        <div className="flex items-center justify-center mb-8">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
            step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'
          }`}>
            1
          </div>
          <div className={`w-16 h-1 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
            step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'
          }`}>
            2
          </div>
        </div>

        {step === 1 && (
          <form onSubmit={handleNextStep} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email *
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name *
              </label>
              <input
                type="text"
                required
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone Number
              </label>
              <input
                type="tel"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="+95 9xxxxxxxxx"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password (Optional)
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="For account recovery (optional)"
              />
              <p className="text-xs text-gray-500 mt-1">
                í²¡ Optional: Set a password for backup access
              </p>
            </div>

            <button
              type="submit"
              className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition"
            >
              Continue to Face Verification â†’
            </button>

            <p className="text-center text-sm text-gray-600">
              Already have an account?{' '}
              <a href="/login" className="text-blue-600 hover:underline font-medium">
                Login
              </a>
            </p>
          </form>
        )}

        {step === 2 && (
          <div>
            <FaceCapture 
              onCapture={handleFaceCapture}
              onCancel={() => setStep(1)}
            />
            {loading && (
              <div className="text-center mt-4">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
                <p className="text-sm text-gray-600 mt-2">Creating your account...</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
