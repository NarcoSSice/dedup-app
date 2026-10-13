import { createBrowserRouter } from 'react-router'

import { Layout } from '@/components/Layout'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { RequestPage } from '@/pages/RequestPage'
import { UploadPage } from '@/pages/UploadPage'

export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <UploadPage /> },
      { path: '/requests/:requestId', element: <RequestPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
