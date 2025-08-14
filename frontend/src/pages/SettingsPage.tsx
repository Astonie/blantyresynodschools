import React, { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Heading,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast,
  VStack,
  HStack,
  Text,
  Button,
  useDisclosure,
  IconButton,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Input,
  Select,
  FormControl,
  FormLabel,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Switch,
  Textarea,
  Checkbox,
  CheckboxGroup,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Card,
  CardBody,
  Flex,
  Spacer,
  Alert,
  AlertIcon,
  Spinner,
  Tooltip,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useColorModeValue
} from '@chakra-ui/react'
import {
  AddIcon,
  EditIcon,
  DeleteIcon,
  ViewIcon,
  SettingsIcon,
  InfoIcon,
  StarIcon,
  LockIcon,
  SearchIcon,
  RepeatIcon
} from '@chakra-ui/icons'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

// Types
interface User {
  id: number
  email: string
  full_name: string
  is_active: boolean
  created_at: string
  updated_at: string
  roles: string[]
}

interface Role {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
  permissions: string[]
  user_count: number
}

interface Permission {
  id: number
  name: string
  description: string | null
  created_at: string
}

interface SystemInfo {
  statistics: {
    total_users: number
    active_users: number
    total_roles: number
    total_permissions: number
  }
  recent_users: Array<{
    email: string
    full_name: string
    created_at: string
  }>
}

export default function SettingsPage() {
  const { user } = useAuth()
  const toast = useToast()
  const [activeTab, setActiveTab] = useState(0)
  
  // Data states
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  
  // Loading states
  const [loading, setLoading] = useState(false)
  const [usersLoading, setUsersLoading] = useState(false)
  const [rolesLoading, setRolesLoading] = useState(false)
  
  // Search and filter states
  const [userSearch, setUserSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  
  // Modal states
  const { isOpen: isUserModalOpen, onOpen: onUserModalOpen, onClose: onUserModalClose } = useDisclosure()
  const { isOpen: isRoleModalOpen, onOpen: onRoleModalOpen, onClose: onRoleModalClose } = useDisclosure()
  const { isOpen: isPermissionModalOpen, onOpen: onPermissionModalOpen, onClose: onPermissionModalClose } = useDisclosure()
  const { isOpen: isRolePermissionModalOpen, onOpen: onRolePermissionModalOpen, onClose: onRolePermissionModalClose } = useDisclosure()
  
  // Form states
  const [userForm, setUserForm] = useState({
    email: '',
    full_name: '',
    password: '',
    is_active: true
  })
  const [roleForm, setRoleForm] = useState({
    name: '',
    description: ''
  })
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingType, setEditingType] = useState<'user' | 'role' | null>(null)
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([])
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [selectedUserRoles, setSelectedUserRoles] = useState<string[]>([])
  
  // Color mode values
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  
  // Load initial data
  useEffect(() => {
    if (user) {
      loadSystemInfo()
      loadUsers()
      loadRoles()
      loadPermissions()
    }
  }, [user])
  
  const loadSystemInfo = async () => {
    try {
      const response = await api.get('/settings/system-info')
      setSystemInfo(response.data)
    } catch (error: any) {
      console.error('Failed to load system info:', error)
    }
  }
  
  const loadUsers = async () => {
    setUsersLoading(true)
    try {
      const params: any = {}
      if (userSearch) params.q = userSearch
      if (roleFilter) params.role = roleFilter
      if (statusFilter) params.status = statusFilter
      
      const response = await api.get('/settings/users', { params })
      setUsers(response.data)
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to load users',
        status: 'error'
      })
    } finally {
      setUsersLoading(false)
    }
  }
  
  const loadRoles = async () => {
    setRolesLoading(true)
    try {
      const response = await api.get('/settings/roles')
      setRoles(response.data)
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to load roles',
        status: 'error'
      })
    } finally {
      setRolesLoading(false)
    }
  }
  
  const loadPermissions = async () => {
    try {
      const response = await api.get('/settings/permissions')
      setPermissions(response.data)
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to load permissions',
        status: 'error'
      })
    }
  }
  
  // User management functions
  const openUserModal = (user?: User) => {
    if (user) {
      setUserForm({
        email: user.email,
        full_name: user.full_name,
        password: '',
        is_active: user.is_active
      })
      setEditingId(user.id)
      setEditingType('user')
    } else {
      setUserForm({
        email: '',
        full_name: '',
        password: '',
        is_active: true
      })
      setEditingId(null)
      setEditingType('user')
    }
    onUserModalOpen()
  }
  
  const handleUserSubmit = async () => {
    try {
      if (editingId) {
        await api.put(`/settings/users/${editingId}`, userForm)
        toast({
          title: 'Success',
          description: 'User updated successfully',
          status: 'success'
        })
      } else {
        await api.post('/settings/users', userForm)
        toast({
          title: 'Success',
          description: 'User created successfully',
          status: 'success'
        })
      }
      onUserModalClose()
      loadUsers()
      loadSystemInfo()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to save user',
        status: 'error'
      })
    }
  }
  
  const deleteUser = async (userId: number) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await api.delete(`/settings/users/${userId}`)
        toast({
          title: 'Success',
          description: 'User deleted successfully',
          status: 'success'
        })
        loadUsers()
        loadSystemInfo()
      } catch (error: any) {
        toast({
          title: 'Error',
          description: error?.response?.data?.detail || 'Failed to delete user',
          status: 'error'
        })
      }
    }
  }
  
  // User-Role assignment functions
  const openUserRoleModal = (user: User) => {
    setSelectedUser(user)
    setSelectedUserRoles(user.roles)
    onPermissionModalOpen()
  }
  
  const handleUserRoleAssignment = async () => {
    if (!selectedUser) return
    
    try {
      // Get current roles for the user
      const currentRoles = selectedUser.roles
      
      // Find roles to add
      const rolesToAdd = selectedUserRoles.filter(r => !currentRoles.includes(r))
      
      // Find roles to remove
      const rolesToRemove = currentRoles.filter(r => !selectedUserRoles.includes(r))
      
      // Add new roles
      for (const roleName of rolesToAdd) {
        const role = roles.find(r => r.name === roleName)
        if (role) {
          await api.post(`/settings/users/${selectedUser.id}/roles`, {
            user_id: selectedUser.id,
            role_id: role.id
          })
        }
      }
      
      // Remove roles
      for (const roleName of rolesToRemove) {
        const role = roles.find(r => r.name === roleName)
        if (role) {
          await api.delete(`/settings/users/${selectedUser.id}/roles/${role.id}`)
        }
      }
      
      toast({
        title: 'Success',
        description: 'User roles updated successfully',
        status: 'success'
      })
      
      onPermissionModalClose()
      loadUsers()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to update user roles',
        status: 'error'
      })
    }
  }
  
  // Role management functions
  const openRoleModal = (role?: Role) => {
    if (role) {
      setRoleForm({
        name: role.name,
        description: role.description || ''
      })
      setEditingId(role.id)
      setEditingType('role')
    } else {
      setRoleForm({
        name: '',
        description: ''
      })
      setEditingId(null)
      setEditingType('role')
    }
    onRoleModalOpen()
  }
  
  const handleRoleSubmit = async () => {
    try {
      if (editingId) {
        await api.put(`/settings/roles/${editingId}`, roleForm)
        toast({
          title: 'Success',
          description: 'Role updated successfully',
          status: 'success'
        })
      } else {
        await api.post('/settings/roles', roleForm)
        toast({
          title: 'Success',
          description: 'Role created successfully',
          status: 'success'
        })
      }
      onRoleModalClose()
      loadRoles()
      loadSystemInfo()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to save role',
        status: 'error'
      })
    }
  }
  
  const deleteRole = async (roleId: number) => {
    if (window.confirm('Are you sure you want to delete this role?')) {
      try {
        await api.delete(`/settings/roles/${roleId}`)
        toast({
          title: 'Success',
          description: 'Role deleted successfully',
          status: 'success'
        })
        loadRoles()
        loadSystemInfo()
      } catch (error: any) {
        toast({
          title: 'Error',
          description: error?.response?.data?.detail || 'Failed to delete role',
          status: 'error'
        })
      }
    }
  }
  
  // Role-Permission management functions
  const openRolePermissionModal = (role: Role) => {
    setSelectedRole(role)
    setSelectedPermissions(role.permissions)
    onRolePermissionModalOpen()
  }
  
  const handlePermissionAssignment = async () => {
    if (!selectedRole) return
    
    try {
      // Get current permissions for the role
      const currentPermissions = selectedRole.permissions
      
      // Find permissions to add
      const permissionsToAdd = selectedPermissions.filter(p => !currentPermissions.includes(p))
      
      // Find permissions to remove
      const permissionsToRemove = currentPermissions.filter(p => !selectedPermissions.includes(p))
      
      // Add new permissions
      for (const permissionName of permissionsToAdd) {
        const permission = permissions.find(p => p.name === permissionName)
        if (permission) {
          await api.post(`/settings/roles/${selectedRole.id}/permissions`, {
            role_id: selectedRole.id,
            permission_id: permission.id
          })
        }
      }
      
      // Remove permissions
      for (const permissionName of permissionsToRemove) {
        const permission = permissions.find(p => p.name === permissionName)
        if (permission) {
          await api.delete(`/settings/roles/${selectedRole.id}/permissions/${permission.id}`)
        }
      }
      
      toast({
        title: 'Success',
        description: 'Role permissions updated successfully',
        status: 'success'
      })
      
      onRolePermissionModalClose()
      loadRoles()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to update role permissions',
        status: 'error'
      })
    }
  }
  
  // Filtered data
  const filteredUsers = users.filter(user => {
    if (userSearch && !user.email.toLowerCase().includes(userSearch.toLowerCase()) && 
        !user.full_name.toLowerCase().includes(userSearch.toLowerCase())) {
      return false
    }
    if (roleFilter && !user.roles.includes(roleFilter)) {
      return false
    }
    if (statusFilter === 'active' && !user.is_active) {
      return false
    }
    if (statusFilter === 'inactive' && user.is_active) {
      return false
    }
    return true
  })
  
  if (!user) {
    return (
      <Container maxW="container.xl" py={8}>
        <Alert status="warning">
          <AlertIcon />
          Please log in to access settings.
        </Alert>
      </Container>
    )
  }
  
  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>System Settings</Heading>
          <Text color="gray.600">Manage users, roles, and permissions</Text>
        </Box>
        
        {/* System Overview Cards */}
        {systemInfo && (
          <SimpleGrid columns={{ base: 1, md: 4 }} spacing={6}>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Total Users</StatLabel>
                  <StatNumber>{systemInfo.statistics.total_users}</StatNumber>
                  <StatHelpText>{systemInfo.statistics.active_users} active</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Total Roles</StatLabel>
                  <StatNumber>{systemInfo.statistics.total_roles}</StatNumber>
                  <StatHelpText>System roles</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Total Permissions</StatLabel>
                  <StatNumber>{systemInfo.statistics.total_permissions}</StatNumber>
                  <StatHelpText>Available permissions</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Recent Activity</StatLabel>
                  <StatNumber>{systemInfo.recent_users.length}</StatNumber>
                  <StatHelpText>New users this week</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </SimpleGrid>
        )}
        
        {/* Main Tabs */}
        <Box bg={bgColor} borderRadius="lg" border="1px" borderColor={borderColor}>
          <Tabs index={activeTab} onChange={setActiveTab} variant="enclosed">
            <TabList>
              <Tab>
                <HStack spacing={2}>
                  <InfoIcon />
                  <Text>Users</Text>
                  <Badge colorScheme="blue" borderRadius="full" px={2}>
                    {users.length}
                  </Badge>
                </HStack>
              </Tab>
              <Tab>
                <HStack spacing={2}>
                  <StarIcon />
                  <Text>Roles</Text>
                  <Badge colorScheme="green" borderRadius="full" px={2}>
                    {roles.length}
                  </Badge>
                </HStack>
              </Tab>
              <Tab>
                <HStack spacing={2}>
                  <LockIcon />
                  <Text>Permissions</Text>
                  <Badge colorScheme="purple" borderRadius="full" px={2}>
                    {permissions.length}
                  </Badge>
                </HStack>
              </Tab>
            </TabList>
            
            <TabPanels>
              {/* Users Tab */}
              <TabPanel>
                <VStack spacing={6} align="stretch">
                  {/* Users Header */}
                  <Flex justify="space-between" align="center">
                    <Heading size="md">User Management</Heading>
                    <Button
                      leftIcon={<AddIcon />}
                      colorScheme="blue"
                      onClick={() => openUserModal()}
                    >
                      Add User
                    </Button>
                  </Flex>
                  
                  {/* Search and Filters */}
                  <HStack spacing={4}>
                    <FormControl maxW="300px">
                      <Input
                        placeholder="Search users..."
                        value={userSearch}
                        onChange={(e) => setUserSearch(e.target.value)}
                        leftIcon={<SearchIcon />}
                      />
                    </FormControl>
                    <FormControl maxW="200px">
                      <Select
                        placeholder="Filter by role"
                        value={roleFilter}
                        onChange={(e) => setRoleFilter(e.target.value)}
                      >
                        {roles.map(role => (
                          <option key={role.id} value={role.name}>
                            {role.name}
                          </option>
                        ))}
                      </Select>
                    </FormControl>
                    <FormControl maxW="150px">
                      <Select
                        placeholder="Status"
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                      >
                        <option value="">All</option>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                      </Select>
                    </FormControl>
                    <Button onClick={loadUsers} isLoading={usersLoading}>
                      Refresh
                    </Button>
                  </HStack>
                  
                  {/* Users Table */}
                  <Box overflowX="auto">
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th>Name</Th>
                          <Th>Email</Th>
                          <Th>Roles</Th>
                          <Th>Status</Th>
                          <Th>Created</Th>
                          <Th>Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {filteredUsers.map(user => (
                          <Tr key={user.id}>
                            <Td fontWeight="medium">{user.full_name}</Td>
                            <Td>{user.email}</Td>
                            <Td>
                              <HStack spacing={1}>
                                {user.roles.map(role => (
                                  <Badge key={role} colorScheme="blue" variant="subtle">
                                    {role}
                                  </Badge>
                                ))}
                              </HStack>
                            </Td>
                            <Td>
                              <Badge
                                colorScheme={user.is_active ? 'green' : 'red'}
                                variant="subtle"
                              >
                                {user.is_active ? 'Active' : 'Inactive'}
                              </Badge>
                            </Td>
                            <Td>{new Date(user.created_at).toLocaleDateString()}</Td>
                            <Td>
                              <HStack spacing={2}>
                                <Tooltip label="Edit user">
                                  <IconButton
                                    aria-label="Edit user"
                                    icon={<EditIcon />}
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => openUserModal(user)}
                                  />
                                </Tooltip>
                                <Tooltip label="Delete user">
                                  <IconButton
                                    aria-label="Delete user"
                                    icon={<DeleteIcon />}
                                    size="sm"
                                    variant="ghost"
                                    colorScheme="red"
                                    onClick={() => deleteUser(user.id)}
                                  />
                                </Tooltip>
                                <Tooltip label="Manage Roles">
                                  <IconButton
                                    aria-label="Manage Roles"
                                    icon={<StarIcon />}
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => openUserRoleModal(user)}
                                  />
                                </Tooltip>
                              </HStack>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                </VStack>
              </TabPanel>
              
              {/* Roles Tab */}
              <TabPanel>
                <VStack spacing={6} align="stretch">
                  {/* Roles Header */}
                  <Flex justify="space-between" align="center">
                    <Heading size="md">Role Management</Heading>
                    <Button
                      leftIcon={<AddIcon />}
                      colorScheme="green"
                      onClick={() => openRoleModal()}
                    >
                      Add Role
                    </Button>
                  </Flex>
                  
                  {/* Roles Table */}
                  <Box overflowX="auto">
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th>Role Name</Th>
                          <Th>Description</Th>
                          <Th>Permissions</Th>
                          <Th>Users</Th>
                          <Th>Created</Th>
                          <Th>Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {roles.map(role => (
                          <Tr key={role.id}>
                            <Td fontWeight="medium">{role.name}</Td>
                            <Td>{role.description || '-'}</Td>
                            <Td>
                              <HStack spacing={1} flexWrap="wrap">
                                {role.permissions.map(permission => (
                                  <Badge key={permission} colorScheme="purple" variant="subtle" fontSize="xs">
                                    {permission}
                                  </Badge>
                                ))}
                              </HStack>
                            </Td>
                            <Td>
                              <Badge colorScheme="blue" variant="subtle">
                                {role.user_count} users
                              </Badge>
                            </Td>
                            <Td>{new Date(role.created_at).toLocaleDateString()}</Td>
                            <Td>
                              <HStack spacing={2}>
                                <Tooltip label="Edit role">
                                  <IconButton
                                    aria-label="Edit role"
                                    icon={<EditIcon />}
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => openRoleModal(role)}
                                  />
                                </Tooltip>
                                <Tooltip label="Delete role">
                                  <IconButton
                                    aria-label="Delete role"
                                    icon={<DeleteIcon />}
                                    size="sm"
                                    variant="ghost"
                                    colorScheme="red"
                                    onClick={() => deleteRole(role.id)}
                                    isDisabled={role.user_count > 0}
                                  />
                                </Tooltip>
                                <Tooltip label="Manage Permissions">
                                  <IconButton
                                    aria-label="Manage Permissions"
                                    icon={<SettingsIcon />}
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => openRolePermissionModal(role)}
                                  />
                                </Tooltip>
                              </HStack>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                </VStack>
              </TabPanel>
              
              {/* Permissions Tab */}
              <TabPanel>
                <VStack spacing={6} align="stretch">
                  <Heading size="md">System Permissions</Heading>
                  <Text color="gray.600">
                    These are the available permissions in the system. Permissions are managed at the role level.
                  </Text>
                  
                  <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
                    {permissions.map(permission => (
                      <Card key={permission.id}>
                        <CardBody>
                          <VStack align="stretch" spacing={3}>
                            <Heading size="sm" color="purple.600">
                              {permission.name}
                            </Heading>
                            <Text fontSize="sm" color="gray.600">
                              {permission.description || 'No description available'}
                            </Text>
                            <Text fontSize="xs" color="gray.500">
                              Created: {new Date(permission.created_at).toLocaleDateString()}
                            </Text>
                          </VStack>
                        </CardBody>
                      </Card>
                    ))}
                  </SimpleGrid>
                </VStack>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Box>
      </VStack>
      
      {/* User Modal */}
      <Modal isOpen={isUserModalOpen} onClose={onUserModalClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {editingId ? 'Edit User' : 'Create New User'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Full Name</FormLabel>
                <Input
                  value={userForm.full_name}
                  onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
                  placeholder="Enter full name"
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  placeholder="Enter email address"
                />
              </FormControl>
              {!editingId && (
                <FormControl isRequired>
                  <FormLabel>Password</FormLabel>
                  <Input
                    type="password"
                    value={userForm.password}
                    onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                    placeholder="Enter password"
                  />
                </FormControl>
              )}
              <FormControl>
                <FormLabel>Active Status</FormLabel>
                <Switch
                  isChecked={userForm.is_active}
                  onChange={(e) => setUserForm({ ...userForm, is_active: e.target.checked })}
                />
                <Text fontSize="sm" color="gray.600" mt={1}>
                  {userForm.is_active ? 'User account is active' : 'User account is inactive'}
                </Text>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onUserModalClose}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={handleUserSubmit}>
              {editingId ? 'Update' : 'Create'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
      
      {/* Role Modal */}
      <Modal isOpen={isRoleModalOpen} onClose={onRoleModalClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {editingId ? 'Edit Role' : 'Create New Role'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Role Name</FormLabel>
                <Input
                  value={roleForm.name}
                  onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })}
                  placeholder="Enter role name"
                />
              </FormControl>
              <FormControl>
                <FormLabel>Description</FormLabel>
                <Textarea
                  value={roleForm.description}
                  onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
                  placeholder="Enter role description"
                  rows={3}
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onRoleModalClose}>
              Cancel
            </Button>
            <Button colorScheme="green" onClick={handleRoleSubmit}>
              {editingId ? 'Update' : 'Create'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Role Permission Modal */}
      <Modal isOpen={isRolePermissionModalOpen} onClose={onRolePermissionModalClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Manage Role Permissions</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Current Permissions for {selectedRole?.name}</FormLabel>
                <CheckboxGroup
                  value={selectedPermissions}
                  onChange={(value) => setSelectedPermissions(value as string[])}
                >
                  {permissions.map(permission => (
                    <Checkbox key={permission.id} value={permission.name}>
                      {permission.name}
                    </Checkbox>
                  ))}
                </CheckboxGroup>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onRolePermissionModalClose}>
              Cancel
            </Button>
            <Button colorScheme="purple" onClick={handlePermissionAssignment}>
              Save Permissions
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* User Role Assignment Modal */}
      <Modal isOpen={isPermissionModalOpen} onClose={onPermissionModalClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Manage User Roles</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Current Roles for {selectedUser?.full_name}</FormLabel>
                <CheckboxGroup
                  value={selectedUserRoles}
                  onChange={(value) => setSelectedUserRoles(value as string[])}
                >
                  {roles.map(role => (
                    <Checkbox key={role.id} value={role.name}>
                      {role.name}
                    </Checkbox>
                  ))}
                </CheckboxGroup>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onPermissionModalClose}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={handleUserRoleAssignment}>
              Save Roles
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Container>
  )
}



