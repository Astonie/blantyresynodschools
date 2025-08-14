import { useState } from 'react'
import { 
  Box, 
  Button, 
  Heading, 
  Input, 
  Stack, 
  useToast, 
  Text, 
  VStack, 
  HStack, 
  FormControl,
  FormLabel,
  FormErrorMessage,
  InputGroup,
  InputRightElement,
  IconButton,
  useDisclosure,
  Image,
  Container,
  Card,
  CardBody,
  Divider
} from '@chakra-ui/react'
import { ViewIcon, ViewOffIcon } from '@chakra-ui/icons'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

export default function LoginPage() {
  const [tenantSlug, setTenantSlug] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  
  const toast = useToast()
  const navigate = useNavigate()

  const login = async () => {
    if (!tenantSlug || !username || !password) {
      toast({ 
        title: 'Missing Information', 
        description: 'Please fill in all fields', 
        status: 'warning' 
      })
      return
    }

    setIsLoading(true)
    try {
      // Set tenant in localStorage first
      localStorage.setItem('tenant', tenantSlug)
      
      // Attempt login
      const res = await api.post('/auth/login', { username, password })
      
      if (res.data.access_token) {
        localStorage.setItem('token', res.data.access_token)
        toast({ 
          title: 'Login Successful', 
          description: 'Welcome to Blantyre Synod Schools', 
          status: 'success' 
        })
        
        // Navigate to the portal
        navigate('/app', { replace: true })
      } else {
        throw new Error('No access token received')
      }
    } catch (error: any) {
      console.error('Login failed:', error)
      
      // Clear tenant if login fails
      localStorage.removeItem('tenant')
      
      let errorMessage = 'Login failed. Please check your credentials.'
      if (error?.response?.status === 401) {
        errorMessage = 'Invalid username or password.'
      } else if (error?.response?.status === 404) {
        errorMessage = 'Tenant not found. Please check the tenant slug.'
      } else if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail
      }
      
      toast({ 
        title: 'Login Failed', 
        description: errorMessage, 
        status: 'error',
        duration: 5000,
        isClosable: true
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      login()
    }
  }

  return (
    <Box minH="100vh" bg="gray.50" py={8}>
      <Container maxW="md">
        <VStack spacing={8}>
          {/* Logo and Title */}
          <VStack spacing={4} textAlign="center">
            <Image 
              src="/logo.jpg" 
              alt="Blantyre Synod Schools" 
              boxSize="80px"
              objectFit="contain"
              fallbackSrc="https://via.placeholder.com/80x80?text=BS"
            />
            <VStack spacing={2}>
              <Heading size="lg" color="blue.600">
                Blantyre Synod Schools
              </Heading>
              <Text color="gray.600" fontSize="md">
                School Management Portal
              </Text>
            </VStack>
          </VStack>

          {/* Login Form */}
          <Card w="100%" shadow="lg">
            <CardBody p={8}>
              <VStack spacing={6} align="stretch">
                <Heading size="md" textAlign="center" color="gray.700">
                  Sign In
                </Heading>
                
                <FormControl isRequired>
                  <FormLabel>Tenant Slug</FormLabel>
                  <Input
                    placeholder="e.g., standrews, domasi-mission, hhi"
                    value={tenantSlug}
                    onChange={(e) => setTenantSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                    onKeyPress={handleKeyPress}
                    size="lg"
                  />
                  <Text fontSize="sm" color="gray.500" mt={1}>
                    Enter your school's unique identifier
                  </Text>
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Username</FormLabel>
                  <Input
                    placeholder="Enter your username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    onKeyPress={handleKeyPress}
                    size="lg"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Password</FormLabel>
                  <InputGroup size="lg">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onKeyPress={handleKeyPress}
                    />
                    <InputRightElement>
                      <IconButton
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                        icon={showPassword ? <ViewOffIcon /> : <ViewIcon />}
                        onClick={() => setShowPassword(!showPassword)}
                        variant="ghost"
                        size="sm"
                      />
                    </InputRightElement>
                  </InputGroup>
                </FormControl>

                <Button
                  colorScheme="blue"
                  size="lg"
                  onClick={login}
                  isLoading={isLoading}
                  loadingText="Signing In..."
                  w="100%"
                >
                  Sign In
                </Button>

                <Divider />

                <VStack spacing={3}>
                  <Text fontSize="sm" color="gray.600" textAlign="center">
                    Need help? Contact your school administrator
                  </Text>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/super-admin')}
                    color="blue.600"
                  >
                    Super Administrator Portal
                  </Button>
                </VStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Footer */}
          <Text fontSize="sm" color="gray.500" textAlign="center">
            © 2025 Blantyre Synod Schools. All rights reserved.
          </Text>
        </VStack>
      </Container>
    </Box>
  )
}


