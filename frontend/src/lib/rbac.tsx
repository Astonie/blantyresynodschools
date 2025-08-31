import { useAuth } from '../lib/auth'

/**
 * RBAC Hook for Frontend Components
 * Provides role and permission-based access control
 */
export function useRBAC() {
  const { user, hasPermission, hasAnyPermission } = useAuth()

  // Check if user has specific role
  const hasRole = (role: string): boolean => {
    if (!user?.roles) return false
    return user.roles.includes(role)
  }

  // Check if user has any of the specified roles
  const hasAnyRole = (roles: string[]): boolean => {
    if (!user?.roles) return false
    return roles.some(role => user.roles.includes(role))
  }

  // Check if user can access a module
  const canAccessModule = (module: string): boolean => {
    if (!user) return false

    switch (module.toLowerCase()) {
      case 'dashboard':
        return true // All authenticated users can access dashboard
      
      case 'students':
        return hasPermission('students.read')
      
      case 'teachers':
        return hasPermission('teachers.read')
      
      case 'academic':
        return hasPermission('academic.read')
      
      case 'finance':
        return hasPermission('finance.read')
      
      case 'communications':
        return hasPermission('communications.read')
      
      case 'library':
        return hasPermission('library.read')
      
      case 'settings':
        return hasPermission('settings.manage')
      
      case 'reports':
        return hasAnyPermission(['reports.view', 'reports.generate'])
      
      case 'parent-portal':
        return hasRole('Parent')
      
      default:
        return false
    }
  }

  // Check if user can perform specific action
  const canPerformAction = (module: string, action: string): boolean => {
    if (!user) return false

    const permission = `${module.toLowerCase()}.${action.toLowerCase()}`
    
    switch (action.toLowerCase()) {
      case 'read':
      case 'view':
        return hasPermission(permission)
      
      case 'create':
      case 'add':
        return hasPermission(permission)
      
      case 'update':
      case 'edit':
        return hasPermission(permission)
      
      case 'delete':
      case 'remove':
        return hasPermission(permission)
      
      case 'manage':
        return hasPermission(permission)
      
      default:
        return hasPermission(permission)
    }
  }

  // Get user's role hierarchy level
  const getRoleLevel = (): number => {
    if (!user?.roles) return 0

    const roleLevels = {
      'Super Administrator': 100,
      'Administrator': 90,
      'School Administrator': 80,
      'Finance Officer': 60,
      'Teacher': 50,
      'Parent': 30,
      'Student': 10
    }

    const userLevels = user.roles.map(role => roleLevels[role] || 0)
    return Math.max(...userLevels, 0)
  }

  // Check if user has higher or equal role level
  const hasMinimumRoleLevel = (requiredLevel: number): boolean => {
    return getRoleLevel() >= requiredLevel
  }

  // Get accessible menu items based on permissions
  const getAccessibleMenuItems = () => {
    const allMenuItems = [
      { 
        key: 'dashboard', 
        label: 'Dashboard', 
        path: '/app',
        icon: 'StarIcon',
        alwaysShow: true 
      },
      { 
        key: 'students', 
        label: 'Students', 
        path: '/app/students',
        icon: 'EditIcon',
        permission: 'students.read'
      },
      { 
        key: 'academic', 
        label: 'Academic', 
        path: '/app/academic',
        icon: 'CalendarIcon',
        permission: 'academic.read'
      },
      { 
        key: 'teachers', 
        label: 'Teachers', 
        path: '/app/teachers',
        icon: 'AtSignIcon',
        permission: 'teachers.read'
      },
      { 
        key: 'finance', 
        label: 'Finance', 
        path: '/app/finance',
        icon: 'CalendarIcon',
        permission: 'finance.read'
      },
      { 
        key: 'communications', 
        label: 'Communications', 
        path: '/app/communications',
        icon: 'ChatIcon',
        permission: 'communications.read'
      },
      { 
        key: 'library', 
        label: 'Library', 
        path: '/app/library',
        icon: 'InfoIcon',
        permission: 'library.read'
      },
      { 
        key: 'settings', 
        label: 'Settings', 
        path: '/app/settings',
        icon: 'SettingsIcon',
        permission: 'settings.manage'
      },
      {
        key: 'parent-portal',
        label: 'My Children',
        path: '/app/parent-portal',
        icon: 'InfoIcon',
        role: 'Parent'
      }
    ]

    return allMenuItems.filter(item => {
      if (item.alwaysShow) return true
      if (item.permission) return hasPermission(item.permission)
      if (item.role) return hasRole(item.role)
      return false
    })
  }

  return {
    user,
    hasRole,
    hasAnyRole,
    hasPermission,
    hasAnyPermission,
    canAccessModule,
    canPerformAction,
    getRoleLevel,
    hasMinimumRoleLevel,
    getAccessibleMenuItems
  }
}

/**
 * Component wrapper for role-based access control
 */
interface RBACWrapperProps {
  children: React.ReactNode
  roles?: string[]
  permissions?: string[]
  requireAll?: boolean
  fallback?: React.ReactNode
}

export function RBACWrapper({ 
  children, 
  roles, 
  permissions, 
  requireAll = false,
  fallback = null 
}: RBACWrapperProps) {
  const { hasAnyRole, hasRole, hasAnyPermission, hasPermission } = useRBAC()

  let hasAccess = true

  if (roles) {
    if (requireAll) {
      hasAccess = roles.every(role => hasRole(role))
    } else {
      hasAccess = hasAnyRole(roles)
    }
  }

  if (permissions && hasAccess) {
    if (requireAll) {
      hasAccess = permissions.every(perm => hasPermission(perm))
    } else {
      hasAccess = hasAnyPermission(permissions)
    }
  }

  return hasAccess ? <>{children}</> : <>{fallback}</>
}

/**
 * Button component with RBAC protection
 */
interface RBACButtonProps {
  roles?: string[]
  permissions?: string[]
  requireAll?: boolean
  children: React.ReactNode
  [key: string]: any // Allow all button props
}

export function RBACButton({ 
  roles, 
  permissions, 
  requireAll = false,
  children, 
  ...buttonProps 
}: RBACButtonProps) {
  return (
    <RBACWrapper roles={roles} permissions={permissions} requireAll={requireAll}>
      <button {...buttonProps}>
        {children}
      </button>
    </RBACWrapper>
  )
}
