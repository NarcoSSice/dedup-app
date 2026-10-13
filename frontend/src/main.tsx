import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { RouterProvider } from 'react-router'

import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { router } from '@/router'
import { store } from '@/store'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Provider store={store}>
      <TooltipProvider>
        <RouterProvider router={router} />
        <Toaster position="top-right" richColors />
      </TooltipProvider>
    </Provider>
  </StrictMode>
)
