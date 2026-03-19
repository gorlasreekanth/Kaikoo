import { GoogleLogin } from '@react-oauth/google'
import { loginWithGoogle } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../components/ui/Toast'

export function LoginPage() {
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()
  const { toast } = useToast()

  const handleSuccess = async (credentialResponse: { credential?: string }) => {
    if (!credentialResponse.credential) return
    try {
      const { access_token, user } = await loginWithGoogle(credentialResponse.credential)
      setAuth(access_token, user)
      navigate('/')
    } catch {
      toast('Login failed. Please try again.', 'error')
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <div className="bg-surface border border-border rounded-2xl p-10 w-full max-w-sm text-center">
        <div className="size-12 rounded-2xl bg-accent/10 flex items-center justify-center mx-auto mb-6">
          <span className="text-2xl">✦</span>
        </div>
        <h1 className="text-xl font-semibold text-text mb-1">Kaikoo</h1>
        <p className="text-text-muted text-sm mb-8">Your personal AI assistant</p>
        <div className="flex justify-center">
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => toast('Google sign-in failed', 'error')}
            theme="filled_black"
            shape="rectangular"
            size="large"
          />
        </div>
      </div>
    </div>
  )
}
