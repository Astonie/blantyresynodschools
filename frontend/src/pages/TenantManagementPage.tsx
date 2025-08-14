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
  Stack,
  Textarea,
  Switch,
  Divider,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Progress,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Grid,
  GridItem
} from '@chakra-ui/react'
import { 
  AddIcon, 
  EditIcon, 
  DeleteIcon, 
  ViewIcon,
  RepeatIcon,
  SettingsIcon,
  DownloadIcon,
  CopyIcon,
  ExternalLinkIcon,
  StarIcon,
  CheckCircleIcon,
  WarningIcon,
  InfoIcon
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
  branding?: {
    logo_url?: string
    primary_color?: string
    secondary_color?: string
    school_name?: string
    motto?: string
  } | null
}

interface TenantStats {
  total_tenants: number
  active_tenants: number
  total_users: number
  total_students: number
  total_teachers: number
  system_health: 'excellent' | 'good' | 'warning' | 'critical'
  storage_usage: number
  last_backup: string
}

export default function TenantManagementPage() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState<TenantStats | null>(null)
  const toast = useToast()
  const navigate = useNavigate()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure()
  const { isOpen: isStatsOpen, onOpen: onStatsOpen, onClose: onStatsClose } = useDisclosure()
  const [editing, setEditing] = useState<Tenant | null>(null)
  const [activeTab, setActiveTab] = useState('overview')
  
  // Form states
  const [modules, setModules] = useState<string[]>([])
  const [contactEmail, setContactEmail] = useState('')
  const [contactPhone, setContactPhone] = useState('')
  const [address, setAddress] = useState('')
  const [description, setDescription] = useState('')
  
  // Create tenant form
  const [createForm, setCreateForm] = useState({
    name: '',
    slug: '',
    description: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    enabled_modules: [] as string[],
    branding: {
      logo_url: '',
      primary_color: '#3182CE',
      secondary_color: '#805AD5',
      school_name: '',
      motto: ''
    }
  })
  
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  const availableModules = [
    'students', 'finance', 'academic', 'teachers', 'communications', 
    'library', 'transport', 'hostel', 'sports', 'events', 'reports'
  ]

  useEffect(() => {
    loadTenants()
    loadStats()
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

  const loadStats = async () => {
    try {
      const response = await superAdminApi.get('/tenants/stats')
      setStats(response.data)
    } catch (error: any) {
      console.error('Failed to load stats:', error)
    }
  }

  const handleCreateTenant = async () => {
    if (!createForm.name || !createForm.slug) {
      return toast({ title: 'Name and slug are required', status: 'warning' })
    }
    
    try {
      await superAdminApi.post('/tenants', createForm)
      toast({
        title: 'Success',
        description: 'Tenant created successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
      onCreateClose()
      setCreateForm({
        name: '', slug: '', description: '', contact_email: '', contact_phone: '', address: '',
        enabled_modules: [], branding: { logo_url: '', primary_color: '#3182CE', secondary_color: '#805AD5', school_name: '', motto: '' }
      })
      loadTenants()
      loadStats()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to create tenant',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
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
      loadStats()
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

  const handleResetTenant = async (tenant: Tenant) => {
    if (!confirm(`Are you sure you want to reset all data for "${tenant.name}"? This will remove all students, teachers, and academic records.`)) {
      return
    }
    
    try {
      await superAdminApi.post(`/tenants/${tenant.id}/reset`)
      toast({
        title: 'Success',
        description: 'Tenant data reset successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
      loadTenants()
      loadStats()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to reset tenant',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
  }

  const openEdit = (tenant: Tenant) => {
    setEditing(tenant)
    setModules(tenant.enabled_modules || [])
    setContactEmail(tenant.contact_email || '')
    setContactPhone(tenant.contact_phone || '')
    setAddress(tenant.address || '')
    setDescription(tenant.description || '')
    onOpen()
  }

  const saveTenant = async () => {
    if (!editing) return
    try {
      await superAdminApi.put(`/tenants/${editing.id}`, {
        enabled_modules: modules,
        contact_email: contactEmail,
        contact_phone: contactPhone,
        address,
        description
      })
      toast({ title: 'Saved', status: 'success' })
      onClose()
      setEditing(null)
      await loadTenants()
    } catch (e: any) {
      toast({ title: 'Save failed', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  const exportTenantData = async (tenant: Tenant) => {
    try {
      const response = await superAdminApi.get(`/tenants/${tenant.id}/export`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${tenant.slug}-data-${new Date().toISOString().split('T')[0]}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast({ title: 'Export successful', status: 'success' })
    } catch (error: any) {
      toast({ title: 'Export failed', description: error?.response?.data?.detail || 'Failed to export data', status: 'error' })
    }
  }

  const getSystemHealthColor = (health: string) => {
    switch (health) {
      case 'excellent': return 'green'
      case 'good': return 'blue'
      case 'warning': return 'yellow'
      case 'critical': return 'red'
      default: return 'gray'
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
            <HStack spacing={3}>
              <Button
                colorScheme="blue"
                leftIcon={<AddIcon />}
                onClick={onCreateOpen}
              >
                Create Tenant
              </Button>
              <Button
                variant="outline"
                leftIcon={<ViewIcon />}
                onClick={onStatsOpen}
              >
                System Stats
              </Button>
            </HStack>
          </Flex>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <Tabs value={activeTab} onChange={setActiveTab} variant="enclosed">
          <TabList>
            <Tab>Overview</Tab>
            <Tab>Tenants</Tab>
            <Tab>Analytics</Tab>
          </TabList>

          <TabPanels>
            {/* Overview Tab */}
            <TabPanel>
              <VStack spacing={8} align="stretch">
                {/* System Health */}
                {stats && (
                  <Card>
                    <CardBody>
                      <Heading size="md" mb={4}>System Health</Heading>
                      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
                        <Stat>
                          <StatLabel>System Status</StatLabel>
                          <StatNumber>
                            <Badge colorScheme={getSystemHealthColor(stats.system_health)} size="lg">
                              {stats.system_health.charAt(0).toUpperCase() + stats.system_health.slice(1)}
                            </Badge>
                          </StatNumber>
                        </Stat>
                        <Stat>
                          <StatLabel>Storage Usage</StatLabel>
                          <StatNumber>{stats.storage_usage}%</StatNumber>
                          <Progress value={stats.storage_usage} colorScheme={stats.storage_usage > 80 ? 'red' : 'green'} />
                        </Stat>
                        <Stat>
                          <StatLabel>Last Backup</StatLabel>
                          <StatNumber>{new Date(stats.last_backup).toLocaleDateString()}</StatNumber>
                        </Stat>
                        <Stat>
                          <StatLabel>Active Tenants</StatLabel>
                          <StatNumber>{stats.active_tenants}/{stats.total_tenants}</StatNumber>
                        </Stat>
                      </SimpleGrid>
                    </CardBody>
                  </Card>
                )}

                {/* Quick Stats */}
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

                {/* Recent Activity */}
                <Card>
                  <CardBody>
                    <Heading size="md" mb={4}>Recent Activity</Heading>
                    <VStack align="stretch" spacing={3}>
                      {tenants.slice(0, 5).map(tenant => (
                        <HStack key={tenant.id} justify="space-between" p={3} bg="gray.50" rounded="md">
                          <VStack align="start" spacing={1}>
                            <Text fontWeight="medium">{tenant.name}</Text>
                            <Text fontSize="sm" color="gray.600">
                              Last updated: {new Date(tenant.updated_at).toLocaleDateString()}
                            </Text>
                          </VStack>
                          <Badge colorScheme={tenant.is_active ? "green" : "red"}>
                            {tenant.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </HStack>
                      ))}
                    </VStack>
                  </CardBody>
                </Card>
              </VStack>
            </TabPanel>

            {/* Tenants Tab */}
            <TabPanel>
              <VStack spacing={8} align="stretch">
                {/* Tenants Table */}
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
                                {(tenant.enabled_modules || []).slice(0,3).join(', ')}
                                {(tenant.enabled_modules && tenant.enabled_modules.length > 3) ? '…' : ''}
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
                                  <Tooltip label="Export Data">
                                    <IconButton
                                      size="sm"
                                      icon={<DownloadIcon />}
                                      aria-label="Export tenant data"
                                      onClick={() => exportTenantData(tenant)}
                                    />
                                  </Tooltip>
                                  <Tooltip label="Reset Data">
                                    <IconButton
                                      size="sm"
                                      icon={<RepeatIcon />}
                                      aria-label="Reset tenant data"
                                      onClick={() => handleResetTenant(tenant)}
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
              </VStack>
            </TabPanel>

            {/* Analytics Tab */}
            <TabPanel>
              <VStack spacing={8} align="stretch">
                <Card>
                  <CardBody>
                    <Heading size="md" mb={4}>Module Usage Analytics</Heading>
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                      {availableModules.map(module => {
                        const usageCount = tenants.filter(t => t.enabled_modules?.includes(module)).length
                        const usagePercentage = (usageCount / tenants.length) * 100
                        return (
                          <Box key={module} p={4} borderWidth="1px" rounded="md">
                            <HStack justify="space-between" mb={2}>
                              <Text fontWeight="medium" textTransform="capitalize">{module}</Text>
                              <Text fontSize="sm" color="gray.600">{usageCount}/{tenants.length}</Text>
                            </HStack>
                            <Progress value={usagePercentage} colorScheme="blue" />
                            <Text fontSize="xs" color="gray.500" mt={1}>
                              {usagePercentage.toFixed(1)}% adoption
                            </Text>
                          </Box>
                        )
                      })}
                    </SimpleGrid>
                  </CardBody>
                </Card>
              </VStack>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Container>

      {/* Edit Tenant Modal */}
      <Modal isOpen={isOpen} onClose={() => { onClose(); setEditing(null) }} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Edit Tenant: {editing?.name}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack align="stretch" spacing={4}>
              <FormControl>
                <FormLabel>Description</FormLabel>
                <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
              </FormControl>
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
                <Textarea value={address} onChange={(e) => setAddress(e.target.value)} />
              </FormControl>
              <FormControl>
                <FormLabel>Enabled Modules</FormLabel>
                <CheckboxGroup value={modules} onChange={(vals) => setModules(vals as string[])}>
                  <Grid templateColumns="repeat(2, 1fr)" gap={2}>
                    {availableModules.map(m => (
                      <Checkbox key={m} value={m}>{m.charAt(0).toUpperCase()+m.slice(1)}</Checkbox>
                    ))}
                  </Grid>
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

      {/* Create Tenant Modal */}
      <Modal isOpen={isCreateOpen} onClose={onCreateClose} size="2xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Create New Tenant</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack align="stretch" spacing={4}>
              <HStack>
                <FormControl isRequired>
                  <FormLabel>Tenant Name</FormLabel>
                  <Input 
                    value={createForm.name} 
                    onChange={(e) => setCreateForm({...createForm, name: e.target.value})}
                    placeholder="e.g., St. Andrews School"
                  />
                </FormControl>
                <FormControl isRequired>
                  <FormLabel>Slug</FormLabel>
                  <Input 
                    value={createForm.slug} 
                    onChange={(e) => setCreateForm({...createForm, slug: e.target.value})}
                    placeholder="e.g., standrews"
                  />
                </FormControl>
              </HStack>
              <FormControl>
                <FormLabel>Description</FormLabel>
                <Textarea 
                  value={createForm.description} 
                  onChange={(e) => setCreateForm({...createForm, description: e.target.value})}
                  placeholder="Brief description of the school"
                />
              </FormControl>
              <HStack>
                <FormControl>
                  <FormLabel>Contact Email</FormLabel>
                  <Input 
                    value={createForm.contact_email} 
                    onChange={(e) => setCreateForm({...createForm, contact_email: e.target.value})}
                    placeholder="admin@school.com"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Contact Phone</FormLabel>
                  <Input 
                    value={createForm.contact_phone} 
                    onChange={(e) => setCreateForm({...createForm, contact_phone: e.target.value})}
                    placeholder="+1234567890"
                  />
                </FormControl>
              </HStack>
              <FormControl>
                <FormLabel>Address</FormLabel>
                <Textarea 
                  value={createForm.address} 
                  onChange={(e) => setCreateForm({...createForm, address: e.target.value})}
                  placeholder="School address"
                />
              </FormControl>
              <Divider />
              <Heading size="sm">Branding & Configuration</Heading>
              <HStack>
                <FormControl>
                  <FormLabel>School Name</FormLabel>
                  <Input 
                    value={createForm.branding.school_name} 
                    onChange={(e) => setCreateForm({
                      ...createForm, 
                      branding: {...createForm.branding, school_name: e.target.value}
                    })}
                    placeholder="Custom school name"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Motto</FormLabel>
                  <Input 
                    value={createForm.branding.motto} 
                    onChange={(e) => setCreateForm({
                      ...createForm, 
                      branding: {...createForm.branding, motto: e.target.value}
                    })}
                    placeholder="School motto"
                  />
                </FormControl>
              </HStack>
              <HStack>
                <FormControl>
                  <FormLabel>Primary Color</FormLabel>
                  <Input 
                    type="color"
                    value={createForm.branding.primary_color} 
                    onChange={(e) => setCreateForm({
                      ...createForm, 
                      branding: {...createForm.branding, primary_color: e.target.value}
                    })}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Secondary Color</FormLabel>
                  <Input 
                    type="color"
                    value={createForm.branding.secondary_color} 
                    onChange={(e) => setCreateForm({
                      ...createForm, 
                      branding: {...createForm.branding, secondary_color: e.target.value}
                    })}
                  />
                </FormControl>
              </HStack>
              <FormControl>
                <FormLabel>Logo URL</FormLabel>
                <Input 
                  value={createForm.branding.logo_url} 
                  onChange={(e) => setCreateForm({
                    ...createForm, 
                    branding: {...createForm.branding, logo_url: e.target.value}
                  })}
                  placeholder="https://example.com/logo.png"
                />
              </FormControl>
              <Divider />
              <Heading size="sm">Enabled Modules</Heading>
              <CheckboxGroup value={createForm.enabled_modules} onChange={(vals) => setCreateForm({...createForm, enabled_modules: vals as string[]})}>
                <Grid templateColumns="repeat(3, 1fr)" gap={2}>
                  {availableModules.map(m => (
                    <Checkbox key={m} value={m}>{m.charAt(0).toUpperCase()+m.slice(1)}</Checkbox>
                  ))}
                </Grid>
              </CheckboxGroup>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant='ghost' mr={3} onClick={onCreateClose}>Cancel</Button>
            <Button colorScheme='blue' onClick={handleCreateTenant}>Create Tenant</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* System Stats Modal */}
      <Modal isOpen={isStatsOpen} onClose={onStatsClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>System Statistics</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {stats ? (
              <VStack align="stretch" spacing={6}>
                <SimpleGrid columns={2} spacing={4}>
                  <Stat>
                    <StatLabel>Total Tenants</StatLabel>
                    <StatNumber>{stats.total_tenants}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Active Tenants</StatLabel>
                    <StatNumber>{stats.active_tenants}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Total Users</StatLabel>
                    <StatNumber>{stats.total_users}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Total Students</StatLabel>
                    <StatNumber>{stats.total_students}</StatNumber>
                  </Stat>
                </SimpleGrid>
                <Divider />
                <Box>
                  <Text fontWeight="medium" mb={2}>System Health</Text>
                  <HStack>
                    <Badge colorScheme={getSystemHealthColor(stats.system_health)} size="lg">
                      {stats.system_health.charAt(0).toUpperCase() + stats.system_health.slice(1)}
                    </Badge>
                    <Text fontSize="sm" color="gray.600">
                      Last checked: {new Date().toLocaleString()}
                    </Text>
                  </HStack>
                </Box>
                <Box>
                  <Text fontWeight="medium" mb={2}>Storage Usage</Text>
                  <Progress value={stats.storage_usage} colorScheme={stats.storage_usage > 80 ? 'red' : 'green'} />
                  <Text fontSize="sm" color="gray.600" mt={1}>
                    {stats.storage_usage}% used
                  </Text>
                </Box>
                <Box>
                  <Text fontWeight="medium" mb={2}>Last Backup</Text>
                  <Text fontSize="sm" color="gray.600">
                    {new Date(stats.last_backup).toLocaleString()}
                  </Text>
                </Box>
              </VStack>
            ) : (
              <Spinner />
            )}
          </ModalBody>
          <ModalFooter>
            <Button onClick={onStatsClose}>Close</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}
