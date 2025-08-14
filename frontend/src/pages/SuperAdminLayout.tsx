import React from 'react'
import { Box, Flex, HStack, VStack, Heading, Button, useColorModeValue } from '@chakra-ui/react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { StarIcon } from '@chakra-ui/icons'

export default function SuperAdminLayout() {
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const navigate = useNavigate()
  const location = useLocation()

  const go = (path: string) => navigate(path)
  const logout = () => {
    localStorage.removeItem('super_admin_token')
    localStorage.removeItem('is_super_admin')
    navigate('/super-admin/login')
  }

  const isActive = (path: string) => location.pathname.startsWith(path)

  return (
    <Flex minH="100vh" bg="gray.50">
      {/* Sidebar */}
      <Box w={{ base: '260px' }} bg={bgColor} borderRight="1px" borderColor={borderColor} p={4} position="sticky" top={0} h="100vh">
        <HStack mb={6} spacing={3}>
          <StarIcon color="blue.500" />
          <Heading size="sm">Platform Admin</Heading>
        </HStack>
        <VStack align="stretch" spacing={2}>
          <Button variant={isActive('/super-admin/dashboard') ? 'solid' : 'ghost'} colorScheme="blue" justifyContent="flex-start" onClick={() => go('/super-admin/dashboard')}>Overview</Button>
          <Button variant={isActive('/super-admin/tenants') ? 'solid' : 'ghost'} colorScheme="blue" justifyContent="flex-start" onClick={() => go('/super-admin/tenants')}>Tenants</Button>
          <Button variant="ghost" justifyContent="flex-start" onClick={() => window.open('mailto:support@example.com')}>Support</Button>
          <Button colorScheme="red" variant="outline" mt={4} onClick={logout}>Logout</Button>
        </VStack>
      </Box>

      {/* Main content */}
      <Box flex="1">
        <Box bg={bgColor} borderBottom="1px" borderColor={borderColor} py={3} px={6} position="sticky" top={0} zIndex={10}>
          <Heading size="md" color="blue.600">Super Administrator</Heading>
        </Box>
        <Box as="main">
          <Outlet />
        </Box>
      </Box>
    </Flex>
  )
}


