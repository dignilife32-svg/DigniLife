// User types
export interface User {
  id: string
  email: string
  full_name: string
  phone_number?: string
  role: 'user' | 'admin' | 'partner' | 'ngo'
  subscription_tier: 'free' | 'pro' | 'premium'
  is_active: boolean
  is_verified: boolean
  kyc_verified: boolean
  total_earnings_usd: number
  available_balance_usd: number
  pending_balance_usd: number
  preferred_currency: string
  current_streak_days: number
  longest_streak_days: number
  created_at: string
}

// Auth types
export interface RegisterRequest {
  email: string
  full_name: string
  phone_number?: string
  password?: string
  face_image_base64: string
}

export interface LoginRequest {
  face_image_base64: string
  email?: string
  password?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

// Task types
export interface Task {
  id: string
  title: string
  description: string
  task_type: string
  difficulty: string
  reward_usd: number
  expected_time_seconds: number
  instructions: string
  is_active: boolean
  created_at: string
}

// Wallet types
export interface Balance {
  available_usd: number
  pending_usd: number
  total_earnings_usd: number
  lifetime_withdrawals_usd: number
  preferred_currency: string
  balance_in_preferred_currency: number
}

export interface WithdrawalRequest {
  amount_usd: number
  currency_code: string
  payout_method: string
  payout_details: Record<string, any>
  face_verification_base64: string
}

// Stats
export interface UserStats {
  total_earnings_usd: number
  available_balance_usd: number
  pending_balance_usd: number
  lifetime_withdrawals_usd: number
  tasks_completed: number
  current_streak_days: number
  longest_streak_days: number
}
