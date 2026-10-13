import { ImagesIcon } from 'lucide-react'
import { Link, Outlet } from 'react-router'

import { RequestSearch } from '@/components/RequestSearch'

export function Layout() {
  return (
    <div className="min-h-svh bg-muted/40">
      <header className="border-b bg-background">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <Link to="/" className="flex items-center gap-2 font-semibold">
            <ImagesIcon className="size-5" />
            Image Duplicate Finder
          </Link>
          <RequestSearch />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
