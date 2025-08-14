import { useState, useEffect } from 'react'
import { 
  Box, 
  Button, 
  Heading, 
  Input, 
  Stack, 
  Select, 
  useToast, 
  Text, 
  VStack, 
  HStack, 
  Divider,
  FormControl,
  FormLabel,
  FormErrorMessage,
  InputGroup,
  InputRightElement,
  IconButton,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Alert,
  AlertIcon
} from '@chakra-ui/react'
import { ViewIcon, ViewOffIcon, AddIcon } from '@chakra-ui/icons'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

interface Tenant {
  id: number
  name: string
  slug: string
}

export default function LoginPage() {
  const [tenant, setTenant] = useState(localStorage.getItem('tenant') || '')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [isOnboarding, setIsOnboarding] = useState(false)
  const [onboardingData, setOnboardingData] = useState({
    name: '',
    slug: '',
    admin_email: '',
    admin_password: ''
  })
  
  const toast = useToast()
  const navigate = useNavigate()
  const { isOpen, onOpen, onClose } = useDisclosure()

  // Load tenants on component mount
  useEffect(() => {
    loadTenants()
  }, [])

  const loadTenants = async () => {
    try {
      const response = await api.get('/tenants')
      setTenants(response.data)
    } catch (error) {
      console.error('Failed to load tenants:', error)
    }
  }

  const login = async () => {
    if (!tenant || !username || !password) {
      toast({ 
        title: 'Missing Information', 
        description: 'Please fill in all fields', 
        status: 'warning' 
      })
      return
    }

    setIsLoading(true)
    try {
      localStorage.setItem('tenant', tenant)
      const res = await api.post('/auth/login', { username, password })
      localStorage.setItem('token', res.data.access_token)
      toast({ 
        title: 'Login Successful', 
        description: 'Welcome to Blantyre Synod Schools', 
        status: 'success' 
      })
      // Navigate to the portal
      navigate('/app', { replace: true })
      // Fallback in case navigation is prevented by state not updating immediately
      setTimeout(() => {
        if (window.location.pathname === '/login') {
          window.location.replace('/app')
        }
      }, 50)
    } catch (e: any) {
      toast({ 
        title: 'Login Failed', 
        description: e?.response?.data?.detail || 'Invalid credentials', 
        status: 'error' 
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleOnboarding = async () => {
    if (!onboardingData.name || !onboardingData.slug || !onboardingData.admin_email || !onboardingData.admin_password) {
      toast({ 
        title: 'Missing Information', 
        description: 'Please fill in all fields', 
        status: 'warning' 
      })
      return
    }

    setIsOnboarding(true)
    try {
      const response = await api.post('/tenants/onboard', onboardingData)
      toast({ 
        title: 'School Created Successfully', 
        description: `${onboardingData.name} has been onboarded`, 
        status: 'success' 
      })
      setTenant(onboardingData.slug)
      setOnboardingData({ name: '', slug: '', admin_email: '', admin_password: '' })
      onClose()
      loadTenants()
    } catch (e: any) {
      toast({ 
        title: 'Onboarding Failed', 
        description: e?.response?.data?.detail || 'Failed to create school', 
        status: 'error' 
      })
    } finally {
      setIsOnboarding(false)
    }
  }

  const generateSlug = (name: string) => {
    return name.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')
  }

  return (
    <Box minH="100vh" bg="gray.50" display="flex" alignItems="center" justifyContent="center">
      <Box maxW="md" w="full" mx="auto" p={8} bg="white" rounded="xl" shadow="lg">
        <VStack spacing={6} align="stretch">
          <Box textAlign="center">
            <Heading size="lg" color="brand.600" mb={2}>
              Blantyre Synod Schools
            </Heading>
            <Text color="gray.600">School Management System</Text>
          </Box>

          <Alert status="info" rounded="md">
            <AlertIcon />
            <Text fontSize="sm">
              Welcome to the Blantyre Synod School Management System. Please sign in to continue.
            </Text>
          </Alert>

          <Stack spacing={4}>
            <FormControl isRequired>
              <FormLabel>School</FormLabel>
              <HStack>
                <Select 
                  placeholder="Select your school" 
                  value={tenant} 
                  onChange={(e) => setTenant(e.target.value)}
                >
                  {tenants.map((t) => (
                    <option key={t.id} value={t.slug}>
                      {t.name}
                    </option>
                  ))}
                </Select>
                <IconButton
                  aria-label="Add new school"
                  icon={<AddIcon />}
                  onClick={onOpen}
                  variant="outline"
                />
              </HStack>
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Email</FormLabel>
              <Input 
                placeholder="Enter your email" 
                type="email" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && login()}
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Password</FormLabel>
              <InputGroup>
                <Input 
                  placeholder="Enter your password" 
                  type={showPassword ? 'text' : 'password'} 
                  value={password} 
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && login()}
                />
                <InputRightElement>
                  <IconButton
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    icon={showPassword ? <ViewOffIcon /> : <ViewIcon />}
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowPassword(!showPassword)}
                  />
                </InputRightElement>
              </InputGroup>
            </FormControl>

            <Button 
              colorScheme="brand" 
              size="lg" 
              onClick={login}
              isLoading={isLoading}
              loadingText="Signing in..."
            >
              Sign In
            </Button>
          </Stack>

          <Divider />

          <Text fontSize="sm" color="gray.500" textAlign="center">
            Need help? Contact your system administrator
          </Text>
        </VStack>
      </Box>

      {/* Onboarding Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Onboard New School</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>School Name</FormLabel>
                <Input 
                  placeholder="Enter school name"
                  value={onboardingData.name}
                  onChange={(e) => {
                    const name = e.target.value
                    setOnboardingData(prev => ({
                      ...prev,
                      name,
                      slug: generateSlug(name)
                    }))
                  }}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>School Slug</FormLabel>
                <Input 
                  placeholder="school-slug"
                  value={onboardingData.slug}
                  onChange={(e) => setOnboardingData(prev => ({ ...prev, slug: e.target.value }))}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Admin Email</FormLabel>
                <Input 
                  placeholder="admin@school.com"
                  type="email"
                  value={onboardingData.admin_email}
                  onChange={(e) => setOnboardingData(prev => ({ ...prev, admin_email: e.target.value }))}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Admin Password</FormLabel>
                <Input 
                  placeholder="Enter admin password"
                  type="password"
                  value={onboardingData.admin_password}
                  onChange={(e) => setOnboardingData(prev => ({ ...prev, admin_password: e.target.value }))}
                />
              </FormControl>

              <Button 
                colorScheme="brand" 
                w="full" 
                onClick={handleOnboarding}
                isLoading={isOnboarding}
                loadingText="Creating School..."
              >
                Create School
              </Button>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  )
}


