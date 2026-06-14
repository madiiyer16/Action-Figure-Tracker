import SignupForm from '@/app/ui/SignupForm'

export default function SignupPage() {
  return (
    <div className="max-w-sm mx-auto px-6 py-16">
      <h1 className="text-2xl font-bold mb-2">Create account</h1>
      <p className="text-zinc-500 text-sm mb-8">
        Track figures and get email alerts when prices drop to your target.
      </p>
      <SignupForm />
    </div>
  )
}
