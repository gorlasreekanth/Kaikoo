import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { ProtectedRoute } from './ProtectedRoute'
import { LoginPage } from '../pages/LoginPage'
import { DashboardPage } from '../pages/DashboardPage'
import { CategoryPage } from '../pages/CategoryPage'
import { SummaryPage } from '../pages/SummaryPage'
import { SettingsPage } from '../pages/SettingsPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { path: '/', element: <DashboardPage /> },
      { path: '/category/:id', element: <CategoryPage /> },
      { path: '/summary/:category_id', element: <SummaryPage /> },
      { path: '/settings', element: <SettingsPage /> },
    ],
  },
])
