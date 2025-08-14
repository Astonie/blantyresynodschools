import { useEffect, useMemo, useState } from 'react'
import { Box, Button, Heading, HStack, Input, Text, useToast, FormControl, FormLabel, Select, VStack, Table, Thead, Tbody, Tr, Th, Td, InputGroup, InputLeftElement, Icon, IconButton, Alert, AlertIcon, Spinner } from '@chakra-ui/react'
import { DeleteIcon, EditIcon } from '@chakra-ui/icons'
import { SearchIcon } from '@chakra-ui/icons'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

type Student = {
  id: number
  first_name: string
  last_name: string
  gender?: string | null
  date_of_birth?: string | null
  admission_no: string
  student_number?: string | null
  current_class?: string | null
}

type Class = {
  id: number
  name: string
  grade_level: string
}

export default function StudentsPage() {
  const { user, isLoading: authLoading } = useAuth()
  const [students, setStudents] = useState<Student[]>([])
  const [classes, setClasses] = useState<Class[]>([])
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ first_name: '', last_name: '', gender: '', current_class: '' })
  const [query, setQuery] = useState('')
  const toast = useToast()

  const loadStudents = async () => {
    if (!user) return
    setLoading(true)
    try {
      const res = await api.get<Student[]>('/students')
      setStudents(res.data)
    } catch (e: any) {
      toast({ title: 'Error loading students', description: e?.response?.data?.detail || String(e), status: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const loadClasses = async () => {
    if (!user) return
    try {
      const res = await api.get<Class[]>('/students/classes/available')
      setClasses(res.data)
    } catch (e: any) {
      console.error('Failed to load classes:', e)
    }
  }

  useEffect(() => {
    if (user && !authLoading) {
      loadStudents()
      loadClasses()
    }
  }, [user, authLoading])

  const create = async () => {
    if (!user) return
    try {
      await api.post('/students', { 
        first_name: form.first_name,
        last_name: form.last_name,
        gender: form.gender || null,
        current_class: form.current_class || null,
      })
      setForm({ first_name: '', last_name: '', gender: '', current_class: '' })
      await loadStudents()
      toast({ title: 'Student created', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  const filteredStudents = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return students
    return students.filter((s) =>
      `${s.first_name} ${s.last_name}`.toLowerCase().includes(q) ||
      s.admission_no.toLowerCase().includes(q) ||
      (s.student_number || '').toLowerCase().includes(q)
    )
  }, [students, query])

  const remove = async (id: number) => {
    if (!user) return
    try {
      await api.delete(`/students/${id}`)
      await loadStudents()
      toast({ title: 'Student deleted', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  if (authLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minH="200px">
        <Spinner size="xl" />
      </Box>
    )
  }

  if (!user) {
    return (
      <Box>
        <Alert status="warning">
          <AlertIcon />
          Please log in to access students.
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      <Heading size="md" mb={4}>Students</Heading>
      <Box mb={4} bg="white" borderWidth="1px" rounded="md" p={4}>
        <VStack spacing={3} align="stretch">
          <HStack>
            <FormControl isRequired>
              <FormLabel>First name</FormLabel>
              <Input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>Last name</FormLabel>
              <Input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
            </FormControl>
          </HStack>
          <HStack>
            <FormControl>
              <FormLabel>Gender</FormLabel>
              <Select placeholder="Select gender" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </Select>
            </FormControl>
            <FormControl>
              <FormLabel>Class</FormLabel>
              <Select placeholder="Select class" value={form.current_class} onChange={(e) => setForm({ ...form, current_class: e.target.value })}>
                {classes.map((cls) => (
                  <option key={cls.id} value={cls.name}>
                    {cls.name} ({cls.grade_level})
                  </option>
                ))}
              </Select>
            </FormControl>
          </HStack>
          <HStack justify="flex-end">
            <Button colorScheme="brand" onClick={create} isLoading={loading}>Add Student</Button>
          </HStack>
        </VStack>
      </Box>
      <Box bg="white" borderWidth="1px" rounded="md" p={4}>
        <HStack mb={3}>
          <InputGroup maxW="360px">
            <InputLeftElement>
              <Icon as={SearchIcon} color="gray.400" />
            </InputLeftElement>
            <Input placeholder="Search by name or admission no" value={query} onChange={(e) => setQuery(e.target.value)} />
          </InputGroup>
        </HStack>
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minH="200px">
            <Spinner size="lg" />
          </Box>
        ) : (
          <Table size="sm" variant="simple">
            <Thead>
              <Tr>
                <Th>Name</Th>
                <Th>Admission No</Th>
                <Th>Class</Th>
                <Th></Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredStudents.map((s) => (
                <Tr key={s.id}>
                  <Td><Text fontWeight="medium">{s.first_name} {s.last_name}</Text></Td>
                  <Td>{s.admission_no}</Td>
                  <Td>{s.current_class || '-'}</Td>
                  <Td isNumeric>
                    <HStack justify="flex-end" spacing={1}>
                      <IconButton aria-label="Edit" size="sm" icon={<EditIcon />} onClick={() => (window.location.href = `/students/${s.id}`)} />
                      <IconButton aria-label="Delete" size="sm" icon={<DeleteIcon />} onClick={() => remove(s.id)} />
                    </HStack>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </Box>
    </Box>
  )
}



