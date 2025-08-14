import React, { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  SimpleGrid,
  Card,
  CardBody,
  Button,
  useToast,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Flex,
  Spacer,
  Alert,
  AlertIcon,
  Spinner,
  useColorModeValue,
  IconButton,
  Tooltip,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  FormControl,
  FormLabel,
  Input,
  Checkbox,
  CheckboxGroup,
  Stack
} from '@chakra-ui/react'
import { 
  AddIcon, 
  EditIcon, 
  DeleteIcon, 
  ViewIcon,
  RepeatIcon,
  SettingsIcon
} from '@chakra-ui/icons'
import { superAdminApi } from '../lib/superAdminApi'
import { useNavigate } from 'react-router-dom'

interface Tenant {
  id: number
  name: string
  slug: string
  description?: string | null
  contact_email?: string | null
  contact_phone?: string | null
  address?: string | null
  is_active?: boolean
  created_at: string
  updated_at: string
  user_count: number
  student_count: number
  teacher_count: number
  enabled_modules?: string[]
}

export default function TenantManagementPage() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const toast = useToast()
  const navigate = useNavigate()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [editing, setEditing] = useState<Tenant | null>(null)
  const [modules, setModules] = useState<string[]>([])
  const [contactEmail, setContactEmail] = useState('')
  const [contactPhone, setContactPhone] = useState('')
  const [address, setAddress] = useState('')
  
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  useEffect(() => {
    loadTenants()
  }, [])

  const loadTenants = async () => {
    try {
      setIsLoading(true)
      const response = await superAdminApi.get('/tenants')
      setTenants(response.data)
    } catch (error: any) {
      console.error('Failed to load tenants:', error)
      toast({
        title: 'Error',
        description: 'Failed to load tenants',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteTenant = async (tenant: Tenant) => {
    if (!confirm(`Are you sure you want to delete tenant "${tenant.name}"? This action cannot be undone.`)) {
      return
    }
    
    try {
      await superAdminApi.delete(`/tenants/${tenant.id}`)
      toast({
        title: 'Success',
        description: 'Tenant deleted successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
      loadTenants()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to delete tenant',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
  }

  const handleTenantAccess = (tenant: Tenant) => {
    localStorage.setItem('tenant', tenant.slug)
    navigate('/app')
  }

  const openEdit = (tenant: Tenant) => {
    setEditing(tenant)
    setModules(tenant.enabled_modules || [])
    setContactEmail(tenant.contact_email || '')
    setContactPhone(tenant.contact_phone || '')
    setAddress(tenant.address || '')
    onOpen()
  }

  const saveTenant = async () => {
    if (!editing) return
    try {
      await superAdminApi.put(`/tenants/${editing.id}`, {
        enabled_modules: modules,
        contact_email: contactEmail,
        contact_phone: contactPhone,
        address
      })
      toast({ title: 'Saved', status: 'success' })
      onClose()
      setEditing(null)
      await loadTenants()
    } catch (e: any) {
      toast({ title: 'Save failed', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  if (isLoading) {
    return (
      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="center">
          <Spinner size="xl" />
          <Text>Loading tenants...</Text>
        </VStack>
      </Container>
    )
  }

  return (
    <Box minH="100vh" bg="gray.50">
      {/* Header */}
      <Box bg={bgColor} borderBottom="1px" borderColor={borderColor} py={4} position="sticky" top={0} zIndex={10}>
        <Container maxW="container.xl">
          <Flex align="center" justify="space-between">
            <VStack align="start" spacing={0}>
              <Heading size="md" color="blue.600">
                Tenant Management
              </Heading>
              <Text fontSize="sm" color="gray.600">
                Manage all school tenants in the system
              </Text>
            </VStack>
            <Button
              colorScheme="blue"
              leftIcon={<AddIcon />}
              onClick={() => toast({ title: 'Coming Soon', description: 'Create tenant feature will be added soon', status: 'info' })}
            >
              Create Tenant
            </Button>
          </Flex>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="stretch">
          {/* Overview Stats */}
          <Box>
            <Heading size="lg" mb={6}>System Overview</Heading>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
              <Card>
                <CardBody>
                  <Text fontSize="2xl" fontWeight="bold" color="blue.600">
                    {tenants.length}
                  </Text>
                  <Text fontSize="sm" color="gray.600">Total Tenants</Text>
                </CardBody>
              </Card>
              <Card>
                <CardBody>
                  <Text fontSize="2xl" fontWeight="bold" color="green.600">
                    {tenants.filter(t => t.is_active).length}
                  </Text>
                  <Text fontSize="sm" color="gray.600">Active Tenants</Text>
                </CardBody>
              </Card>
              <Card>
                <CardBody>
                  <Text fontSize="2xl" fontWeight="bold" color="purple.600">
                    {tenants.reduce((sum, t) => sum + t.user_count, 0)}
                  </Text>
                  <Text fontSize="sm" color="gray.600">Total Users</Text>
                </CardBody>
              </Card>
              <Card>
                <CardBody>
                  <Text fontSize="2xl" fontWeight="bold" color="orange.600">
                    {tenants.reduce((sum, t) => sum + t.student_count, 0)}
                  </Text>
                  <Text fontSize="sm" color="gray.600">Total Students</Text>
                </CardBody>
              </Card>
            </SimpleGrid>
          </Box>

          {/* Tenants Table */}
          <Box>
            <Heading size="lg" mb={6}>All Tenants</Heading>
            <Card>
              <CardBody>
                <Box overflowX="auto">
                  <Table variant="simple">
                    <Thead>
                      <Tr>
                        <Th>Tenant Name</Th>
                        <Th>Slug</Th>
                        <Th>Status</Th>
                        <Th>Modules</Th>
                        <Th>Users</Th>
                        <Th>Students</Th>
                        <Th>Teachers</Th>
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
                          <Td>
                            <Badge 
                              colorScheme={tenant.is_active ? "green" : "red"} 
                              variant="subtle"
                            >
                              {tenant.is_active ? "Active" : "Inactive"}
                            </Badge>
                          </Td>
                          <Td>
                            {(tenant.enabled_modules || []).slice(0,3).join(', ')}{(tenant.enabled_modules && tenant.enabled_modules.length > 3) ? '…' : ''}
                          </Td>
                          <Td>{tenant.user_count}</Td>
                          <Td>{tenant.student_count}</Td>
                          <Td>{tenant.teacher_count}</Td>
                          <Td>
                            <HStack spacing={2}>
                              <Tooltip label="View Statistics">
                                <IconButton
                                  size="sm"
                                  icon={<ViewIcon />}
                                  aria-label="View statistics"
                                  onClick={() => toast({ title: 'Coming Soon', description: 'Statistics feature will be added soon', status: 'info' })}
                                />
                              </Tooltip>
                              <Tooltip label="Edit Tenant">
                                <IconButton
                                  size="sm"
                                  icon={<EditIcon />}
                                  aria-label="Edit tenant"
                                  onClick={() => openEdit(tenant)}
                                />
                              </Tooltip>
                              <Tooltip label="Access Tenant">
                                <IconButton
                                  size="sm"
                                  icon={<SettingsIcon />}
                                  aria-label="Access tenant"
                                  onClick={() => handleTenantAccess(tenant)}
                                />
                              </Tooltip>
                              <Tooltip label="Reset Data">
                                <IconButton
                                  size="sm"
                                  icon={<RepeatIcon />}
                                  aria-label="Reset tenant data"
                                  onClick={() => toast({ title: 'Coming Soon', description: 'Reset feature will be added soon', status: 'info' })}
                                />
                              </Tooltip>
                              <Tooltip label="Delete Tenant">
                                <IconButton
                                  size="sm"
                                  icon={<DeleteIcon />}
                                  aria-label="Delete tenant"
                                  colorScheme="red"
                                  onClick={() => handleDeleteTenant(tenant)}
                                />
                              </Tooltip>
                            </HStack>
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

      {/* Edit Modal */}
      <Modal isOpen={isOpen} onClose={() => { onClose(); setEditing(null) }}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Edit Tenant</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack align="stretch" spacing={4}>
              <FormControl>
                <FormLabel>Contact Email</FormLabel>
                <Input value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} />
              </FormControl>
              <FormControl>
                <FormLabel>Contact Phone</FormLabel>
                <Input value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
              </FormControl>
              <FormControl>
                <FormLabel>Address</FormLabel>
                <Input value={address} onChange={(e) => setAddress(e.target.value)} />
              </FormControl>
              <FormControl>
                <FormLabel>Enabled Modules</FormLabel>
                <CheckboxGroup value={modules} onChange={(vals) => setModules(vals as string[])}>
                  <Stack spacing={2} direction='column'>
                    {['students','finance','academic','teachers','communications'].map(m => (
                      <Checkbox key={m} value={m}>{m.charAt(0).toUpperCase()+m.slice(1)}</Checkbox>
                    ))}
                  </Stack>
                </CheckboxGroup>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant='ghost' mr={3} onClick={onClose}>Cancel</Button>
            <Button colorScheme='blue' onClick={saveTenant}>Save</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}
