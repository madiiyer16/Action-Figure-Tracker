import LoginForm from '@/app/ui/LoginForm'

export default function LoginPage() {
  return (
    <div className="max-w-sm mx-auto px-6 py-16">
      <h1 className="text-2xl font-bold mb-2">Sign in</h1>
      <p className="text-zinc-500 text-sm mb-8">
        Sign in to manage your watchlist and get price alerts.
      </p>
      <LoginForm />
    </div>
  )
}
