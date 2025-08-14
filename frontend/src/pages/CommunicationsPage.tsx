import React, { useEffect, useState } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  useToast,
  Card,
  CardBody,
  CardHeader,
  Input,
  Textarea,
  Select,
  SimpleGrid,
  Tag,
  TagLabel,
  Badge,
  Divider,
  IconButton,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  FormControl,
  FormLabel,
  InputGroup,
  InputLeftElement,
  Spinner,
} from '@chakra-ui/react'
import { AddIcon, SearchIcon, CheckIcon, DeleteIcon } from '@chakra-ui/icons'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

interface Announcement {
  id: number
  title: string
  content: string
  audience_type: 'all' | 'role' | 'class'
  audience_value?: string
  is_published: boolean
  scheduled_at?: string | null
  published_at?: string | null
  created_by: number
  created_by_name?: string
  created_at: string
  updated_at: string
}

export default function CommunicationsPage() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showPublishedOnly, setShowPublishedOnly] = useState<boolean | undefined>(undefined)
  const [creating, setCreating] = useState(false)

  const toast = useToast()
  const { user } = useAuth()
  const canManage = user?.permissions?.includes('communications.manage') || user?.permissions?.includes('communications.send')

  const {
    isOpen: isCreateOpen,
    onOpen: onCreateOpen,
    onClose: onCreateClose,
  } = useDisclosure()

  const [form, setForm] = useState({
    title: '',
    content: '',
    audience_type: 'all' as 'all' | 'role' | 'class',
    audience_value: '',
    scheduled_at: ''
  })

  const loadAnnouncements = async () => {
    try {
      setIsLoading(true)
      const params = new URLSearchParams()
      if (search) params.append('search', search)
      if (showPublishedOnly !== undefined) params.append('published', String(showPublishedOnly))
      const res = await api.get(`/communications/announcements?${params}`)
      setAnnouncements(res.data)
    } catch (e) {
      toast({ title: 'Error', description: 'Failed to load announcements', status: 'error' })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => { loadAnnouncements() }, [])

  const createAnnouncement = async () => {
    if (!form.title || !form.content) {
      toast({ title: 'Missing fields', description: 'Title and content are required', status: 'warning' })
      return
    }
    setCreating(true)
    try {
      await api.post('/communications/announcements', null, {
        params: {
          title: form.title,
          content: form.content,
          audience_type: form.audience_type,
          audience_value: form.audience_value || undefined,
          scheduled_at: form.scheduled_at || undefined
        }
      })
      toast({ title: 'Created', description: 'Announcement created', status: 'success' })
      onCreateClose()
      setForm({ title: '', content: '', audience_type: 'all', audience_value: '', scheduled_at: '' })
      loadAnnouncements()
    } catch (e: any) {
      toast({ title: 'Failed', description: e?.response?.data?.detail || 'Failed to create announcement', status: 'error' })
    } finally {
      setCreating(false)
    }
  }

  const publishAnnouncement = async (ann: Announcement) => {
    try {
      await api.post(`/communications/announcements/${ann.id}/publish`)
      toast({ title: 'Published', description: 'Announcement published', status: 'success' })
      loadAnnouncements()
    } catch (e: any) {
      toast({ title: 'Failed', description: e?.response?.data?.detail || 'Failed to publish', status: 'error' })
    }
  }

  const deleteAnnouncement = async (ann: Announcement) => {
    if (!confirm(`Delete announcement "${ann.title}"?`)) return
    try {
      await api.delete(`/communications/announcements/${ann.id}`)
      toast({ title: 'Deleted', description: 'Announcement deleted', status: 'success' })
      loadAnnouncements()
    } catch (e: any) {
      toast({ title: 'Failed', description: e?.response?.data?.detail || 'Failed to delete', status: 'error' })
    }
  }

  return (
    <Box minH="100vh" bg="gray.50">
      <Box bg="white" borderBottom="1px" borderColor="gray.200" py={4}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={0}>
              <Heading size="md" color="blue.600">Communications</Heading>
              <Text fontSize="sm" color="gray.600">Announce and communicate with your school community</Text>
            </VStack>
            {canManage && (
              <Button colorScheme="blue" leftIcon={<AddIcon />} onClick={onCreateOpen}>New Announcement</Button>
            )}
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <VStack spacing={6} align="stretch">
          <Card>
            <CardBody>
              <HStack>
                <InputGroup>
                  <InputLeftElement>
                    <SearchIcon color="gray.400" />
                  </InputLeftElement>
                  <Input placeholder="Search announcements..." value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && loadAnnouncements()} />
                </InputGroup>
                <Select width="240px" value={String(showPublishedOnly)} onChange={(e) => setShowPublishedOnly(e.target.value === 'undefined' ? undefined : e.target.value === 'true')}>
                  <option value="undefined">All</option>
                  <option value="true">Published</option>
                  <option value="false">Drafts</option>
                </Select>
                <Button onClick={loadAnnouncements}>Filter</Button>
              </HStack>
            </CardBody>
          </Card>

          {isLoading ? (
            <VStack py={8}><Spinner size="xl" /><Text>Loading...</Text></VStack>
          ) : (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              {announcements.map((ann) => (
                <Card key={ann.id} shadow="md" _hover={{ shadow: 'lg' }}>
                  <CardHeader pb={0}>
                    <VStack align="start" spacing={2}>
                      <HStack spacing={3}>
                        <Badge colorScheme={ann.is_published ? 'green' : 'yellow'}>{ann.is_published ? 'Published' : 'Draft'}</Badge>
                        <Tag size="sm" variant="subtle">
                          <TagLabel>
                            {ann.audience_type === 'all' ? 'All Users' : ann.audience_type === 'role' ? `Role: ${ann.audience_value}` : `Class: ${ann.audience_value}`}
                          </TagLabel>
                        </Tag>
                      </HStack>
                      <Heading size="md" noOfLines={2}>{ann.title}</Heading>
                      <Text noOfLines={3} color="gray.700">{ann.content}</Text>
                    </VStack>
                  </CardHeader>
                  <CardBody>
                    <VStack align="stretch" spacing={3}>
                      <Text fontSize="sm" color="gray.500">By {ann.created_by_name || 'Unknown'} • {new Date(ann.created_at).toLocaleString()}</Text>
                      <HStack justify="space-between">
                        <HStack>
                          {canManage && !ann.is_published && (
                            <Button size="sm" colorScheme="green" leftIcon={<CheckIcon />} onClick={() => publishAnnouncement(ann)}>Publish</Button>
                          )}
                        </HStack>
                        {canManage && (
                          <IconButton aria-label="Delete" icon={<DeleteIcon />} size="sm" colorScheme="red" variant="ghost" onClick={() => deleteAnnouncement(ann)} />
                        )}
                      </HStack>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          )}
        </VStack>
      </Container>

      <Modal isOpen={isCreateOpen} onClose={onCreateClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>New Announcement</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <FormControl isRequired>
                <FormLabel>Title</FormLabel>
                <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Content</FormLabel>
                <Textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} rows={6} />
              </FormControl>
              <HStack>
                <FormControl>
                  <FormLabel>Audience Type</FormLabel>
                  <Select value={form.audience_type} onChange={(e) => setForm({ ...form, audience_type: e.target.value as any })}>
                    <option value="all">All Users</option>
                    <option value="role">By Role</option>
                    <option value="class">By Class</option>
                  </Select>
                </FormControl>
                {(form.audience_type === 'role' || form.audience_type === 'class') && (
                  <FormControl>
                    <FormLabel>Audience Value</FormLabel>
                    <Input value={form.audience_value} onChange={(e) => setForm({ ...form, audience_value: e.target.value })} placeholder={form.audience_type === 'role' ? 'e.g., Teacher' : 'e.g., Form 2A'} />
                  </FormControl>
                )}
              </HStack>
              <FormControl>
                <FormLabel>Schedule (optional)</FormLabel>
                <Input type="datetime-local" value={form.scheduled_at} onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })} />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onCreateClose}>Cancel</Button>
            <Button colorScheme="blue" onClick={createAnnouncement} isLoading={creating}>Create</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}



