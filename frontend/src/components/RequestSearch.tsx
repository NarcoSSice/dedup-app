import { SearchIcon } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function RequestSearch() {
  const [requestId, setRequestId] = useState('')
  const navigate = useNavigate()

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    const id = requestId.trim()
    if (!id) return
    navigate(`/requests/${encodeURIComponent(id)}`)
    setRequestId('')
  }

  return (
    <form onSubmit={onSubmit} className="flex w-full gap-2 sm:w-96">
      <Input
        value={requestId}
        onChange={(e) => setRequestId(e.target.value)}
        placeholder="Open results by request ID"
        aria-label="Request ID"
      />
      <Button type="submit" variant="outline" disabled={!requestId.trim()}>
        <SearchIcon />
        Open
      </Button>
    </form>
  )
}
