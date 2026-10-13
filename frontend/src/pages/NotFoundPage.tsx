import { Link } from 'react-router'

import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <p className="text-lg font-semibold">Page not found</p>
      <Button asChild variant="outline">
        <Link to="/">Back to upload</Link>
      </Button>
    </div>
  )
}
