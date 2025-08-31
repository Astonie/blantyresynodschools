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

  useEffect(() => {
    const fetchChildren = async () => {
      try {
        const response = await api.get('/parents/children')
        setChildren(response.data || [])
      } catch (error) {
        console.error('Error fetching children:', error)
      }
    }

    const fetchUnreadCommunications = async () => {
      try {
        const response = await api.get('/communications', {
          params: { unread_only: true }
        })
        setUnreadCount(response.data?.length || 0)
      } catch (error) {
        console.error('Error fetching unread communications:', error)
      }
    }

    if (user) {
      fetchChildren()
      fetchUnreadCommunications()
    }
  }, [user])

  const logout = () => {
    localStorage.removeItem('token')
    navigate('/login', { replace: true })
  }

  // Check if user has parent role
  const isParent = user?.roles?.includes('Parent') || user?.roles?.includes('Parent (Restricted)')

  if (!isParent) {
    return (
      <Box p={6}>
        <Alert status="error">
          <AlertIcon />
          Access Denied: This area is only accessible to parents.
        </Alert>
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
          <ParentNavItem to="/app/parent" icon={<FaHome />}>
            Dashboard
          </ParentNavItem>
          
          <ParentNavItem to="/app/parent/children" icon={<FaChild />}>
            My Children
            <Badge ml={2} colorScheme="blue" fontSize="xs">
              {children.length}
            </Badge>
          </ParentNavItem>

          <ParentNavItem to="/app/parent/academic" icon={<FaGraduationCap />}>
            Academic Progress
          </ParentNavItem>

          <ParentNavItem to="/app/parent/communications" icon={<FaComments />}>
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
                  onClick={() => navigate(`/app/parent/child/${child.id}`)}
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
            onClick={() => navigate('/app/parent/communications')}
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
              <MenuItem onClick={() => navigate('/app/parent/profile')}>
                My Profile
              </MenuItem>
              <MenuItem onClick={() => navigate('/app/parent/settings')}>
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
              <ParentNavItem to="/app/parent" onNavigate={onClose} icon={<FaHome />}>
                Dashboard
              </ParentNavItem>
              <ParentNavItem to="/app/parent/children" onNavigate={onClose} icon={<FaChild />}>
                My Children
              </ParentNavItem>
              <ParentNavItem to="/app/parent/academic" onNavigate={onClose} icon={<FaGraduationCap />}>
                Academic Progress
              </ParentNavItem>
              <ParentNavItem to="/app/parent/communications" onNavigate={onClose} icon={<FaComments />}>
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
  return (
    <NavLink
      to={to}
      style={({ isActive }) => ({
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
      })}
      onClick={onNavigate}
    >
      {icon}
      <span>{children}</span>
    </NavLink>
  )
}
