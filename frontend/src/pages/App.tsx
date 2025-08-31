import { Navigate, Route, Routes } from 'react-router-dom'
import { Container } from '@chakra-ui/react'
import LandingPage from './LandingPage'
import LoginPage from './LoginPage'
import SuperAdminLoginPage from './SuperAdminLoginPage'
import SuperAdminDashboard from './SuperAdminDashboard'
import SuperAdminLayout from './SuperAdminLayout'
import TenantManagementPage from './TenantManagementPage'
import DashboardPage from './DashboardPage'
import StudentsPage from './StudentsPage'
import FinancePage from './FinancePage'
import AcademicPage from './AcademicPage'
import TeachersPage from './TeachersPage'
import CommunicationsPage from './CommunicationsPage'
import SettingsPage from './SettingsPage'
import LibraryPage from './LibraryPage'
import StudentDetailsPage from './StudentDetailsPage'
import ParentDashboard from './ParentDashboard'
import { ParentChildrenPage } from './ParentChildrenPage'
import { ChildDetailsPage } from './ChildDetailsPage'
import TeacherDashboard from './TeacherDashboard'
import TeacherGradeManagement from './TeacherGradeManagement'
import TeacherAttendanceManagement from './TeacherAttendanceManagement'
import { AppShell } from '../ui/AppShell'
import { ParentLayout } from '../components/ParentLayout'
import { AuthProvider, useAuth } from '../lib/auth'

const isAuthed = () => !!localStorage.getItem('token')
const isSuperAdminAuthed = () => !!localStorage.getItem('super_admin_token')

function RequireParentRole({ children }: { children: React.ReactNode }) {
  const { isLoading, user, error } = useAuth()
  
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
  
  if (error) {
    console.error('ParentRole Auth Error:', error)
    return (
      <Container>
        <div style={{ textAlign: 'center', padding: '2rem', color: 'red' }}>
          <h2>Authentication Error</h2>
          <p>Error: {error}</p>
          <p>Check console for more details</p>
        </div>
      </Container>
    )
  }
  
  const isParent = user.roles?.includes('Parent') || user.roles?.includes('Parent (Restricted)')
  if (!isParent) {
    console.warn('Access denied for user:', {
      userId: user.id,
      email: user.email,
      roles: user.roles,
      permissions: user.permissions
    })
    return (
      <Container>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <h2>Access Denied</h2>
          <p>This area is only accessible to parents.</p>
          <p>Your roles: {user.roles?.join(', ') || 'None'}</p>
          <p>Debug: Check console for user details</p>
        </div>
      </Container>
    )
  }
  
  return <>{children}</>
}

function RequireTeacherRole({ children }: { children: React.ReactNode }) {
  const { isLoading, user } = useAuth()
  
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
  
  const isTeacher = user.roles?.includes('Teacher') || user.roles?.includes('Head Teacher')
  if (!isTeacher) {
    return (
      <Container>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <h2>Access Denied</h2>
          <p>This area is only accessible to teachers.</p>
          <p>Your roles: {user.roles?.join(', ') || 'None'}</p>
        </div>
      </Container>
    )
  }
  
  return <>{children}</>
}

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
            element={isSuperAdminAuthed() ? <SuperAdminLayout /> : <Navigate to="/super-admin/login" replace />}
          >
            <Route path="dashboard" element={<SuperAdminDashboard />} />
            {/* Super admin routes do not use tenant permission guard */}
            <Route path="tenants" element={<TenantManagementPage />} />
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
          <Route path="library" element={<RequirePermission perms={["library.read"]}><LibraryPage /></RequirePermission>} />
          <Route path="settings" element={<RequirePermission perms={["settings.manage"]}><SettingsPage /></RequirePermission>} />
        </Route>

        {/* Parent-specific routes */}
        <Route
          path="/parent"
          element={isAuthed() ? (
            <RequireParentRole>
              <ParentLayout />
            </RequireParentRole>
          ) : <Navigate to="/login" replace />}
        >
          <Route index element={<ParentDashboard />} />
          <Route path="children" element={<ParentChildrenPage />} />
          <Route path="child/:childId" element={<ChildDetailsPage />} />
          <Route path="child/:childId/academic" element={<ChildDetailsPage />} />
          <Route path="child/:childId/communications" element={<ChildDetailsPage />} />
          <Route path="academic" element={<ParentChildrenPage />} />
          <Route path="academic/:childId" element={<ChildDetailsPage />} />
          <Route path="communications" element={<CommunicationsPage />} />
          <Route path="profile" element={<ParentDashboard />} />
          <Route path="settings" element={<ParentDashboard />} />
          <Route path="*" element={<div style={{padding: '2rem'}}><h3>Parent Route Not Found</h3><p>The requested parent route was not found.</p></div>} />
        </Route>

        {/* Teacher-specific routes */}
        <Route
          path="/teacher"
          element={isAuthed() ? (
            <RequireTeacherRole>
              <AppShell />
            </RequireTeacherRole>
          ) : <Navigate to="/login" replace />}
        >
          <Route index element={<Navigate to="/teacher/dashboard" replace />} />
          <Route path="dashboard" element={<TeacherDashboard />} />
          <Route path="grades/:className/:subjectCode" element={<TeacherGradeManagement />} />
          <Route path="grades" element={<TeacherGradeManagement />} />
          <Route path="attendance/:className" element={<TeacherAttendanceManagement />} />
          <Route path="attendance" element={<TeacherAttendanceManagement />} />
          <Route path="classes/:className/:subjectCode" element={<TeacherGradeManagement />} />
          <Route path="communications" element={<CommunicationsPage />} />
        </Route>
        
        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}



