import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { GenerateForm } from '@/components/GenerateForm'

export default async function NewPlanPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth?next=/plans/new')

  return (
    <div className="flex flex-1 flex-col page-bg px-6 py-12">
      <GenerateForm />
    </div>
  )
}
