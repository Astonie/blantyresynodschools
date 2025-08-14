import React, { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  useToast,
  Input,
  InputGroup,
  InputLeftElement,
  Card,
  CardBody,
  SimpleGrid,
  Spinner,
  useColorModeValue
} from '@chakra-ui/react'
import { SearchIcon, AddIcon, DownloadIcon } from '@chakra-ui/icons'
import { api } from '../lib/api'

interface LibraryResource {
  id: number
  title: string
  description?: string
  author?: string
  category?: string
  file_size?: number
  upload_date: string
  download_count: number
}

export default function LibraryPage() {
  const [resources, setResources] = useState<LibraryResource[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  
  const toast = useToast()
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  useEffect(() => {
    loadResources()
  }, [])

  const loadResources = async () => {
    try {
      setIsLoading(true)
      const response = await api.get('/library/resources')
      setResources(response.data)
    } catch (error: any) {
      console.error('Failed to load resources:', error)
      toast({
        title: 'Error',
        description: 'Failed to load library resources',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = () => {
    loadResources()
  }

  const handleDownload = async (resource: LibraryResource) => {
    try {
      const response = await api.get(`/library/resources/${resource.id}/download`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${resource.title}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      
      toast({
        title: 'Download Started',
        description: 'File download has begun',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
      
      loadResources()
    } catch (error: any) {
      toast({
        title: 'Download Failed',
        description: 'Failed to download resource',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown'
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <Box minH="100vh" bg="gray.50">
      {/* Header */}
      <Box bg={bgColor} borderBottom="1px" borderColor={borderColor} py={4}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={0}>
              <Heading size="md" color="blue.600">
                Library Management
              </Heading>
              <Text fontSize="sm" color="gray.600">
                Access and manage study materials and resources
              </Text>
            </VStack>
            <Button colorScheme="blue" leftIcon={<AddIcon />}>
              Upload Resource
            </Button>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="stretch">
          {/* Search */}
          <Card>
            <CardBody>
              <HStack>
                <InputGroup>
                  <InputLeftElement>
                    <SearchIcon color="gray.400" />
                  </InputLeftElement>
                  <Input
                    placeholder="Search resources..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                </InputGroup>
                <Button colorScheme="blue" onClick={handleSearch}>
                  Search
                </Button>
              </HStack>
            </CardBody>
          </Card>

          {/* Resources */}
          {isLoading ? (
            <VStack spacing={4} py={8}>
              <Spinner size="xl" />
              <Text>Loading resources...</Text>
            </VStack>
          ) : (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              {resources.map((resource) => (
                <Card key={resource.id} shadow="md">
                  <CardBody>
                    <VStack align="stretch" spacing={3}>
                      <Heading size="md">{resource.title}</Heading>
                      {resource.description && (
                        <Text color="gray.600">{resource.description}</Text>
                      )}
                      
                      <VStack align="start" spacing={1} fontSize="sm">
                        {resource.author && (
                          <Text><strong>Author:</strong> {resource.author}</Text>
                        )}
                        <Text><strong>Size:</strong> {formatFileSize(resource.file_size)}</Text>
                        <Text><strong>Uploaded:</strong> {formatDate(resource.upload_date)}</Text>
                        <Text><strong>Downloads:</strong> {resource.download_count}</Text>
                      </VStack>

                      <Button
                        colorScheme="blue"
                        leftIcon={<DownloadIcon />}
                        onClick={() => handleDownload(resource)}
                      >
                        Download
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          )}
        </VStack>
      </Container>
    </Box>
  )
}
