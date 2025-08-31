import React, { useState, useEffect } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  Flex,
  HStack,
  Spacer,
  Text,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Avatar,
  useDisclosure,
  VStack,
  Badge,
  Image,
  Alert,
  AlertIcon
} from '@chakra-ui/react'
import { HamburgerIcon, BellIcon } from '@chakra-ui/icons'
import { FaChild, FaComments, FaGraduationCap, FaHome } from 'react-icons/fa'
import { useAuth } from '../lib/auth'
import { api } from '../lib/api'

interface Child {
  id: number
  first_name: string
  last_name: string
  admission_no: string
  class_name?: string
}

export function ParentLayout() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [children, setChildren] = useState<Child[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [tenant, setTenant] = useState(localStorage.getItem('tenant') || '')
  const [apiErrors, setApiErrors] = useState<string[]>([])

  useEffect(() => {
    const fetchChildren = async () => {
      try {
        console.log('ParentLayout: Fetching children for user:', user?.email)
        console.log('ParentLayout: Current tenant:', tenant)
        console.log('ParentLayout: Token exists:', !!localStorage.getItem('token'))
        
        const response = await api.get('/parents/children')
        console.log('ParentLayout: Children API response:', response.data)
        setChildren(response.data || [])
        
        // Remove error if successful
        setApiErrors(prev => prev.filter(err => !err.includes('children')))
      } catch (error: any) {
        console.error('ParentLayout: Error fetching children:', {
          status: error?.response?.status,
          statusText: error?.response?.statusText,
          data: error?.response?.data,
          message: error?.message,
          url: error?.config?.url,
          headers: error?.config?.headers
        })
        
        const errorMsg = `Children API Error: ${error?.response?.status} - ${error?.response?.data?.detail || error?.message}`
        setApiErrors(prev => [...prev.filter(err => !err.includes('children')), errorMsg])
      }
    }

    const fetchUnreadCommunications = async () => {
      try {
        console.log('ParentLayout: Fetching unread communications')
        // Communications API not implemented yet - set to 0
        setUnreadCount(0)
        
        // Remove error if successful
        setApiErrors(prev => prev.filter(err => !err.includes('communications')))
      } catch (error: any) {
        console.error('ParentLayout: Error fetching communications:', {
          status: error?.response?.status,
          statusText: error?.response?.statusText,
          data: error?.response?.data,
          message: error?.message
        })
        
        const errorMsg = `Communications API Error: ${error?.response?.status} - ${error?.response?.data?.detail || error?.message}`
        setApiErrors(prev => [...prev.filter(err => !err.includes('communications')), errorMsg])
      }
    }

    if (user) {
      fetchChildren()
      fetchUnreadCommunications()
    }
  }, [user, tenant])

  const logout = () => {
    console.log('ParentLayout: Manual logout triggered')
    localStorage.removeItem('token')
    localStorage.removeItem('tenant')
    navigate('/login', { replace: true })
  }

  // Check if user has parent role
  const isParent = user?.roles?.includes('Parent') || user?.roles?.includes('Parent (Restricted)')

  console.log('ParentLayout: User role check:', {
    user: user?.email,
    roles: user?.roles,
    isParent,
    tenant
  })

  if (!isParent) {
    console.warn('ParentLayout: Access denied - user is not a parent:', {
      userId: user?.id,
      email: user?.email,
      roles: user?.roles,
      permissions: user?.permissions
    })
    
    return (
      <Box p={6}>
        <Alert status="error" mb={4}>
          <AlertIcon />
          Access Denied: This area is only accessible to parents.
        </Alert>
        <Box bg="gray.50" p={4} borderRadius="md">
          <Text fontSize="sm" fontWeight="bold" mb={2}>Debug Information:</Text>
          <Text fontSize="xs">User: {user?.email}</Text>
          <Text fontSize="xs">Roles: {user?.roles?.join(', ') || 'None'}</Text>
          <Text fontSize="xs">Expected: Parent or Parent (Restricted)</Text>
          <Text fontSize="xs">Check console for full user object</Text>
        </Box>
      </Box>
    )
  }

  return (
    <Flex minH="100vh" bg="gray.50">
      {/* Parent Sidebar */}
      <Box 
        as="aside" 
        display={{ base: 'none', md: 'block' }} 
        w="280px" 
        bg="white" 
        borderRightWidth="1px" 
        position="sticky" 
        top={0} 
        h="100vh"
        boxShadow="sm"
      >
        {/* Header */}
        <Flex p={4} align="center" borderBottomWidth="1px" bg="blue.50">
          <HStack spacing={3}>
            <Box w="32px" h="32px">
              <Image
                src="/logo.jpg"
                alt="School Logo"
                w="full"
                h="full"
                objectFit="contain"
              />
            </Box>
            <VStack align="start" spacing={0}>
              <Text fontWeight="bold" color="blue.600" fontSize="lg">
                Parent Portal
              </Text>
              <Text fontSize="xs" color="gray.600">
                {children.length} {children.length === 1 ? 'Child' : 'Children'}
              </Text>
            </VStack>
          </HStack>
        </Flex>

        {/* Navigation Menu */}
        <VStack align="stretch" spacing={1} p={3}>
          <ParentNavItem to="/parent" icon={<FaHome />}>
            Dashboard
          </ParentNavItem>
          
          <ParentNavItem to="/parent/children" icon={<FaChild />}>
            My Children
            <Badge ml={2} colorScheme="blue" fontSize="xs">
              {children.length}
            </Badge>
          </ParentNavItem>

          <ParentNavItem to="/parent/academic" icon={<FaGraduationCap />}>
            Academic Progress
          </ParentNavItem>

          <ParentNavItem to="/parent/communications" icon={<FaComments />}>
            Communications
            {unreadCount > 0 && (
              <Badge ml={2} colorScheme="red" fontSize="xs">
                {unreadCount}
              </Badge>
            )}
          </ParentNavItem>
        </VStack>

        {/* Children Quick Access */}
        {children.length > 0 && (
          <Box mt={6} px={3}>
            <Text fontSize="sm" fontWeight="bold" color="gray.600" mb={3}>
              Quick Access
            </Text>
            <VStack align="stretch" spacing={2}>
              {children.slice(0, 3).map((child) => (
                <Box
                  key={child.id}
                  p={2}
                  borderRadius="md"
                  bg="gray.50"
                  cursor="pointer"
                  _hover={{ bg: 'blue.50' }}
                  onClick={() => navigate(`/parent/child/${child.id}`)}
                >
                  <HStack>
                    <Avatar size="sm" name={`${child.first_name} ${child.last_name}`} />
                    <VStack align="start" spacing={0} flex={1}>
                      <Text fontSize="sm" fontWeight="medium">
                        {child.first_name} {child.last_name}
                      </Text>
                      <Text fontSize="xs" color="gray.500">
                        {child.class_name || 'No Class'} • {child.admission_no}
                      </Text>
                    </VStack>
                  </HStack>
                </Box>
              ))}
              {children.length > 3 && (
                <Text fontSize="xs" color="blue.500" textAlign="center" mt={2}>
                  +{children.length - 3} more children
                </Text>
              )}
            </VStack>
          </Box>
        )}
      </Box>

      {/* Content area */}
      <Flex direction="column" flex="1">
        {/* Top Header */}
        <Flex as="header" p={4} bg="white" borderBottomWidth="1px" align="center" gap={4}>
          <IconButton 
            aria-label="Open menu" 
            icon={<HamburgerIcon />} 
            variant="ghost" 
            display={{ base: 'inline-flex', md: 'none' }} 
            onClick={onOpen} 
          />
          
          <Text fontSize="lg" fontWeight="bold" color="blue.600">
            Welcome, {user?.full_name?.split(' ')[0] || 'Parent'}
          </Text>
          
          <Spacer />

          {/* Notifications */}
          <IconButton
            aria-label="Notifications"
            icon={<BellIcon />}
            variant="ghost"
            position="relative"
            onClick={() => navigate('/parent/communications')}
          >
            {unreadCount > 0 && (
              <Badge
                position="absolute"
                top="-1px"
                right="-1px"
                colorScheme="red"
                borderRadius="full"
                fontSize="xs"
                minW="18px"
                h="18px"
              >
                {unreadCount > 9 ? '9+' : unreadCount}
              </Badge>
            )}
          </IconButton>

          {/* User Menu */}
          <Menu>
            <MenuButton as={Button} rightIcon={<Avatar size="sm" name={user?.full_name || user?.email} />}>
              {user?.full_name?.split(' ')[0] || 'Parent'}
            </MenuButton>
            <MenuList>
              <MenuItem onClick={() => navigate('/parent/profile')}>
                My Profile
              </MenuItem>
              <MenuItem onClick={() => navigate('/parent/settings')}>
                Settings
              </MenuItem>
              <MenuItem onClick={logout} color="red.500">
                Logout
              </MenuItem>
            </MenuList>
          </Menu>
        </Flex>

        {/* Main Content */}
        <Box flex="1" bg="gray.50">
          {/* Development Debug Info */}
          {apiErrors.length > 0 && (
            <Alert status="warning" m={4} mb={2}>
              <AlertIcon />
              <VStack align="start" spacing={1} flex={1}>
                <Text fontWeight="bold" fontSize="sm">API Errors (Development Mode):</Text>
                {apiErrors.map((error, index) => (
                  <Text key={index} fontSize="xs" fontFamily="mono">
                    {error}
                  </Text>
                ))}
              </VStack>
            </Alert>
          )}
          
          {/* Debug information for development */}
          {process.env.NODE_ENV === 'development' && (
            <Box bg="yellow.50" border="1px" borderColor="yellow.200" m={4} p={3} borderRadius="md" fontSize="xs">
              <Text fontWeight="bold" mb={2}>Development Debug Info:</Text>
              <Text>Tenant: {tenant}</Text>
              <Text>User: {user?.email}</Text>
              <Text>Roles: {user?.roles?.join(', ')}</Text>
              <Text>Children Count: {children.length}</Text>
              <Text>Token Present: {!!localStorage.getItem('token')}</Text>
              <Text>API Base URL: {import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}</Text>
            </Box>
          )}
          
          <Outlet />
        </Box>
      </Flex>

      {/* Mobile Menu */}
      {isOpen && (
        <Box position="fixed" inset={0} bg="blackAlpha.600" zIndex={20} onClick={onClose}>
          <Box bg="white" w="280px" h="100%" onClick={(e) => e.stopPropagation()}>
            <Box p={4} borderBottomWidth="1px">
              <Text fontWeight="bold" color="blue.600">Parent Portal</Text>
            </Box>
            <VStack align="stretch" spacing={2} p={3}>
              <ParentNavItem to="/parent" onNavigate={onClose} icon={<FaHome />}>
                Dashboard
              </ParentNavItem>
              <ParentNavItem to="/parent/children" onNavigate={onClose} icon={<FaChild />}>
                My Children
              </ParentNavItem>
              <ParentNavItem to="/parent/academic" onNavigate={onClose} icon={<FaGraduationCap />}>
                Academic Progress
              </ParentNavItem>
              <ParentNavItem to="/parent/communications" onNavigate={onClose} icon={<FaComments />}>
                Communications
              </ParentNavItem>
              <Button onClick={() => { onClose(); logout(); }} variant="ghost" justifyContent="flex-start" color="red.500" mt={4}>
                Logout
              </Button>
            </VStack>
          </Box>
        </Box>
      )}
    </Flex>
  )
}

interface ParentNavItemProps {
  to: string
  children: React.ReactNode
  icon?: React.ReactNode
  onNavigate?: () => void
}

function ParentNavItem({ to, children, icon, onNavigate }: ParentNavItemProps) {
  const handleClick = (e: React.MouseEvent) => {
    console.log('ParentNavItem clicked:', { to, children: children?.toString() })
    if (onNavigate) {
      onNavigate()
    }
  }
  
  return (
    <NavLink
      to={to}
      style={({ isActive }) => {
        console.log('ParentNavItem rendering:', { to, isActive })
        return {
          background: isActive ? 'var(--chakra-colors-blue-50)' : 'transparent',
          borderRadius: '8px',
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontWeight: '500',
          color: isActive ? 'var(--chakra-colors-blue-600)' : 'var(--chakra-colors-gray-700)',
          borderLeft: isActive ? '3px solid var(--chakra-colors-blue-500)' : '3px solid transparent',
          transition: 'all 0.2s'
        }
      }}
      onClick={handleClick}
    >
      {icon}
      <span>{children}</span>
    </NavLink>
  )
}
