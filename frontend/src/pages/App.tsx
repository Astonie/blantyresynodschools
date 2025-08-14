import { Navigate, Route, Routes } from 'react-router-dom'
import { Container } from '@chakra-ui/react'
import LandingPage from './LandingPage'
import LoginPage from './LoginPage'
import SuperAdminLoginPage from './SuperAdminLoginPage'
import SuperAdminDashboard from './SuperAdminDashboard'
import DashboardPage from './DashboardPage'
import StudentsPage from './StudentsPage'
import FinancePage from './FinancePage'
import AcademicPage from './AcademicPage'
import TeachersPage from './TeachersPage'
import CommunicationsPage from './CommunicationsPage'
import SettingsPage from './SettingsPage'
import StudentDetailsPage from './StudentDetailsPage'
import { AppShell } from '../ui/AppShell'
import { AuthProvider, useAuth } from '../lib/auth'

const isAuthed = () => !!localStorage.getItem('token')
const isSuperAdminAuthed = () => !!localStorage.getItem('super_admin_token')

function RequirePermission({ perms, children }: { perms: string[]; children: React.ReactNode }) {
  const { isLoading, user, hasAnyPermission } = useAuth()
  
  if (isLoading) {
    return (
      <Container display="flex" justifyContent="center" alignItems="center" minH="200px">
        Loading...
      </Container>
    )
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  if (!hasAnyPermission(perms)) {
    return (
      <Container>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <h2>Access Denied</h2>
          <p>You don't have permission to access this page.</p>
          <p>Required permissions: {perms.join(', ')}</p>
          <p>Your permissions: {user.permissions?.join(', ') || 'None'}</p>
        </div>
      </Container>
    )
  }
  
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        
        {/* Authentication routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/super-admin/login" element={<SuperAdminLoginPage />} />
        
        {/* Super Admin routes */}
        <Route
          path="/super-admin"
          element={isSuperAdminAuthed() ? <SuperAdminDashboard /> : <Navigate to="/super-admin/login" replace />}
        >
          <Route path="dashboard" element={<SuperAdminDashboard />} />
        </Route>
        
        {/* Protected application routes */}
        <Route
          path="/app"
          element={isAuthed() ? <AppShell /> : <Navigate to="/login" replace />}
        >
          <Route index element={<DashboardPage />} />
          <Route path="students" element={<RequirePermission perms={["students.read"]}><StudentsPage /></RequirePermission>} />
          <Route path="students/:id" element={<RequirePermission perms={["students.read"]}><StudentDetailsPage /></RequirePermission>} />
          <Route path="finance" element={<RequirePermission perms={["finance.read"]}><FinancePage /></RequirePermission>} />
          <Route path="academic" element={<RequirePermission perms={["academic.read"]}><AcademicPage /></RequirePermission>} />
          <Route path="teachers" element={<RequirePermission perms={["teachers.read"]}><TeachersPage /></RequirePermission>} />
          <Route path="communications" element={<CommunicationsPage />} />
          <Route path="settings" element={<RequirePermission perms={["settings.manage"]}><SettingsPage /></RequirePermission>} />
        </Route>
        
        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}



