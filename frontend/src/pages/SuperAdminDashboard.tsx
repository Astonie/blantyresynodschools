import React, { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  SimpleGrid,
  Card,
  CardBody,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Button,
  Select,
  useToast,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Alert,
  AlertIcon,
  Spinner,
  useColorModeValue,
  HStack
} from '@chakra-ui/react'
import { SettingsIcon, ArrowForwardIcon } from '@chakra-ui/icons'
import { superAdminApi } from '../lib/superAdminApi'
import { useNavigate } from 'react-router-dom'

interface Tenant {
  id: number
  name: string
  slug: string
  users: number
  active_users: number
  roles: number
  permissions: number
}

interface SystemStats {
  total_users: number
  active_users: number
  total_roles: number
  total_permissions: number
  total_tenants: number
}

export default function SuperAdminDashboard() {
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null)
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [selectedTenant, setSelectedTenant] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingStats, setIsLoadingStats] = useState(false)
  const toast = useToast()
  const navigate = useNavigate()
  
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  useEffect(() => {
    loadSystemInfo()
  }, [])

  const loadSystemInfo = async () => {
    try {
      setIsLoadingStats(true)
      const response = await superAdminApi.get('/settings/super-admin/system-info')
      
      const data = response.data
      setSystemStats(data.statistics)
      setTenants(data.tenants)
      
      if (data.tenants.length > 0) {
        setSelectedTenant(data.tenants[0].slug)
      }
    } catch (error: any) {
      console.error('Failed to load system info:', error)
      toast({
        title: 'Error',
        description: 'Failed to load system information',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
      setIsLoadingStats(false)
    }
  }

  const handleTenantAccess = (tenantSlug: string) => {
    // Store the selected tenant and redirect to the main app
    localStorage.setItem('tenant', tenantSlug)
    localStorage.removeItem('is_super_admin')
    localStorage.removeItem('super_admin_token')
    navigate('/app')
  }

  const handleLogout = () => {
    localStorage.removeItem('super_admin_token')
    localStorage.removeItem('is_super_admin')
    navigate('/super-admin/login')
  }

  if (isLoading) {
    return (
      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="center">
          <Spinner size="xl" />
          <Text>Loading system information...</Text>
        </VStack>
      </Container>
    )
  }

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={8} align="stretch">
          {/* System Overview */}
          <Box>
            <Heading size="lg" mb={6}>System Overview</Heading>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>Total Tenants</StatLabel>
                    <StatNumber>{systemStats?.total_tenants || 0}</StatNumber>
                    <StatHelpText>Active school tenants</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>Total Users</StatLabel>
                    <StatNumber>{systemStats?.total_users || 0}</StatNumber>
                    <StatHelpText>{systemStats?.active_users || 0} active</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>Total Roles</StatLabel>
                    <StatNumber>{systemStats?.total_roles || 0}</StatNumber>
                    <StatHelpText>System-wide roles</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>Total Permissions</StatLabel>
                    <StatNumber>{systemStats?.total_permissions || 0}</StatNumber>
                    <StatHelpText>Available permissions</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </SimpleGrid>
          </Box>

          {/* Tenant Management */}
          <Box>
            <Heading size="lg" mb={6}>Tenant Management</Heading>
            <Alert status="info" mb={6} borderRadius="md">
              <AlertIcon />
              <Text fontSize="sm">
                Select a tenant to access its specific settings and management features. 
                You can manage users, roles, and permissions for each individual school.
              </Text>
            </Alert>

            <Card>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  <HStack justify="space-between">
                    <Text fontWeight="semibold">Select Tenant to Manage:</Text>
                    <Select
                      value={selectedTenant}
                      onChange={(e) => setSelectedTenant(e.target.value)}
                      maxW="300px"
                    >
                      {tenants.map(tenant => (
                        <option key={tenant.id} value={tenant.slug}>
                          {tenant.name}
                        </option>
                      ))}
                    </Select>
                  </HStack>

                  {selectedTenant && (
                    <Box>
                      <Text fontWeight="semibold" mb={4}>Tenant Details:</Text>
                      <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4}>
                        <Box textAlign="center" p={4} bg="blue.50" borderRadius="md">
                          <Text fontSize="2xl" fontWeight="bold" color="blue.600">
                            {tenants.find(t => t.slug === selectedTenant)?.users || 0}
                          </Text>
                          <Text fontSize="sm" color="gray.600">Total Users</Text>
                        </Box>
                        <Box textAlign="center" p={4} bg="green.50" borderRadius="md">
                          <Text fontSize="2xl" fontWeight="bold" color="green.600">
                            {tenants.find(t => t.slug === selectedTenant)?.active_users || 0}
                          </Text>
                          <Text fontSize="sm" color="gray.600">Active Users</Text>
                        </Box>
                        <Box textAlign="center" p={4} bg="purple.50" borderRadius="md">
                          <Text fontSize="2xl" fontWeight="bold" color="purple.600">
                            {tenants.find(t => t.slug === selectedTenant)?.roles || 0}
                          </Text>
                          <Text fontSize="sm" color="gray.600">Roles</Text>
                        </Box>
                        <Box textAlign="center" p={4} bg="orange.50" borderRadius="md">
                          <Text fontSize="2xl" fontWeight="bold" color="orange.600">
                            {tenants.find(t => t.slug === selectedTenant)?.permissions || 0}
                          </Text>
                          <Text fontSize="sm" color="gray.600">Permissions</Text>
                        </Box>
                      </SimpleGrid>
                    </Box>
                  )}

                  <HStack spacing={4}>
                    <Button
                      colorScheme="blue"
                      leftIcon={<SettingsIcon />}
                      onClick={() => handleTenantAccess(selectedTenant)}
                      isDisabled={!selectedTenant}
                    >
                      Access Tenant Settings
                    </Button>
                    <Button
                      variant="outline"
                      leftIcon={<ArrowForwardIcon />}
                      onClick={() => handleTenantAccess(selectedTenant)}
                      isDisabled={!selectedTenant}
                    >
                      Go to Tenant Dashboard
                    </Button>
                    <Button
                      colorScheme="purple"
                      variant="outline"
                      onClick={() => navigate('/super-admin/tenants')}
                    >
                      Manage All Tenants
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </Box>

          {/* All Tenants Table */}
          <Box>
            <Heading size="lg" mb={6}>All Tenants Overview</Heading>
            <Card>
              <CardBody>
                <Box overflowX="auto">
                  <Table variant="simple">
                    <Thead>
                      <Tr>
                        <Th>Tenant Name</Th>
                        <Th>Slug</Th>
                        <Th>Users</Th>
                        <Th>Active Users</Th>
                        <Th>Roles</Th>
                        <Th>Permissions</Th>
                        <Th>Actions</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {tenants.map(tenant => (
                        <Tr key={tenant.id}>
                          <Td fontWeight="medium">{tenant.name}</Td>
                          <Td>
                            <Badge colorScheme="blue" variant="subtle">
                              {tenant.slug}
                            </Badge>
                          </Td>
                          <Td>{tenant.users}</Td>
                          <Td>
                            <Badge colorScheme="green" variant="subtle">
                              {tenant.active_users}
                            </Badge>
                          </Td>
                          <Td>{tenant.roles}</Td>
                          <Td>{tenant.permissions}</Td>
                          <Td>
                            <Button
                              size="sm"
                              colorScheme="blue"
                              variant="outline"
                              onClick={() => handleTenantAccess(tenant.slug)}
                            >
                              Access
                            </Button>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              </CardBody>
            </Card>
          </Box>
      </VStack>
    </Container>
  )
}
