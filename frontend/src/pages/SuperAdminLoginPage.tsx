import React, { useState } from 'react'
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Text,
  useToast,
  Alert,
  AlertIcon,
  InputGroup,
  InputRightElement,
  IconButton,
  Card,
  CardBody,
  Image,
  HStack,
  Divider
} from '@chakra-ui/react'
import { ViewIcon, ViewOffIcon, LockIcon } from '@chakra-ui/icons'
import { api } from '../lib/api'
import { useNavigate } from 'react-router-dom'

export default function SuperAdminLoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const toast = useToast()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!username || !password) {
      toast({
        title: 'Error',
        description: 'Please fill in all fields',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    setIsLoading(true)
    
    try {
      const response = await api.post('/auth/super-admin/login', {
        username,
        password
      })
      
      const { access_token } = response.data
      
      // Store the super admin token
      localStorage.setItem('super_admin_token', access_token)
      localStorage.setItem('is_super_admin', 'true')
      
      toast({
        title: 'Success',
        description: 'Super Administrator login successful',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
      
      // Redirect to super admin dashboard
      navigate('/super-admin/dashboard')
      
    } catch (error: any) {
      console.error('Login error:', error)
      toast({
        title: 'Login Failed',
        description: error?.response?.data?.detail || 'Invalid credentials or not a Super Administrator',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Box minH="100vh" bg="gray.50" py={10}>
      <Container maxW="md">
        <VStack spacing={8}>
          {/* Logo and Title */}
          <VStack spacing={4}>
            <Box 
              w="80px" 
              h="80px" 
              position="relative"
            >
              <Image
                src="/logo.jpg"
                alt="CCAP Blantyre Synod Logo"
                w="full"
                h="full"
                objectFit="contain"
              />
            </Box>
            <VStack spacing={2}>
              <Heading size="lg" color="brand.600">
                Super Administrator Portal
              </Heading>
              <Text color="gray.600" textAlign="center">
                Access system-wide administration and management
              </Text>
            </VStack>
          </VStack>

          {/* Login Form */}
          <Card w="full" shadow="lg">
            <CardBody p={8}>
              <form onSubmit={handleSubmit}>
                <VStack spacing={6}>
                  <Alert status="info" borderRadius="md">
                    <AlertIcon />
                    <Text fontSize="sm">
                      This portal is for Super Administrators only. 
                      You must have Super Administrator privileges to access this system.
                    </Text>
                  </Alert>

                  <FormControl isRequired>
                    <FormLabel>Email Address</FormLabel>
                    <Input
                      type="email"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Enter your email address"
                      size="lg"
                    />
                  </FormControl>

                  <FormControl isRequired>
                    <FormLabel>Password</FormLabel>
                    <InputGroup size="lg">
                      <Input
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter your password"
                      />
                      <InputRightElement>
                        <IconButton
                          aria-label={showPassword ? 'Hide password' : 'Show password'}
                          icon={showPassword ? <ViewOffIcon /> : <ViewIcon />}
                          variant="ghost"
                          onClick={() => setShowPassword(!showPassword)}
                        />
                      </InputRightElement>
                    </InputGroup>
                  </FormControl>

                  <Button
                    type="submit"
                    colorScheme="blue"
                    size="lg"
                    w="full"
                    isLoading={isLoading}
                    loadingText="Signing in..."
                    leftIcon={<LockIcon />}
                  >
                    Sign in as Super Administrator
                  </Button>
                </VStack>
              </form>
            </CardBody>
          </Card>

          {/* Footer */}
          <VStack spacing={4}>
            <Divider />
            <Text color="gray.500" fontSize="sm" textAlign="center">
              Blantyre Synod Schools Management System
            </Text>
            <Text color="gray.400" fontSize="xs" textAlign="center">
              Super Administrator Portal - Secure Access Only
            </Text>
          </VStack>
        </VStack>
      </Container>
    </Box>
  )
}
