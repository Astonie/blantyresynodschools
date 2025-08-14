import { useEffect, useMemo, useState } from 'react'
import {
  Box,
  Heading,
  Text,
  Table,
  Thead,
  Tr,
  Th,
  Tbody,
  Td,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Input,
  Button,
  Switch,
  useToast,
  InputGroup,
  InputLeftElement,
  Icon,
  IconButton,
} from '@chakra-ui/react'
import { SearchIcon, EditIcon } from '@chakra-ui/icons'
import { api } from '../lib/api'

type Teacher = {
  id: number
  email: string
  full_name: string
  is_active: boolean
  phone?: string | null
  address?: string | null
  date_of_birth?: string | null
  hire_date?: string | null
  qualification?: string | null
  specialization?: string | null
  salary?: number | null
}

export default function TeachersPage() {
  const toast = useToast()
  const [teachers, setTeachers] = useState<Teacher[]>([])
  const [query, setQuery] = useState('')
  const [form, setForm] = useState({
    email: '',
    full_name: '',
    phone: '',
    address: '',
    qualification: '',
    specialization: '',
    salary: '',
  })
  const [editing, setEditing] = useState<Teacher | null>(null)
  const [tempPassword, setTempPassword] = useState<string | null>(null)
  const [classes, setClasses] = useState<Array<{ id:number; name:string }>>([])
  const [subjects, setSubjects] = useState<Array<{ id:number; name:string }>>([])
  const [assignment, setAssignment] = useState({ teacher_id: '', class_id: '', subject_id: '', academic_year: '', is_primary: false })

  const load = async () => {
    const [t, c, s] = await Promise.all([
      api.get<Teacher[]>('/teachers'),
      api.get('/academic/classes').catch(() => ({ data: [] })),
      api.get('/academic/subjects').catch(() => ({ data: [] })),
    ])
    setTeachers(t.data)
    setClasses(c.data)
    setSubjects(s.data)
  }

  useEffect(() => { load() }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return teachers
    return teachers.filter(t =>
      t.full_name.toLowerCase().includes(q) || t.email.toLowerCase().includes(q)
    )
  }, [teachers, query])

  const createTeacher = async () => {
    if (!form.email || !form.full_name) {
      return toast({ title: 'Email and full name are required', status: 'warning' })
    }
    try {
      const res = await api.post('/teachers', {
        email: form.email,
        full_name: form.full_name,
        phone: form.phone || null,
        address: form.address || null,
        qualification: form.qualification || null,
        specialization: form.specialization || null,
        salary: form.salary ? Number(form.salary) : null,
      })
      setTempPassword(res.data?.temp_password || null)
      setForm({ email: '', full_name: '', phone: '', address: '', qualification: '', specialization: '', salary: '' })
      await load()
      toast({ title: 'Teacher created', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  const toggleActive = async (t: Teacher) => {
    try {
      await api.put(`/teachers/${t.id}`, { is_active: !t.is_active })
      await load()
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  const saveEdit = async () => {
    if (!editing) return
    try {
      await api.put(`/teachers/${editing.id}`, {
        full_name: editing.full_name,
        phone: editing.phone,
        address: editing.address,
        qualification: editing.qualification,
        specialization: editing.specialization,
        salary: editing.salary,
      })
      setEditing(null)
      await load()
      toast({ title: 'Teacher updated', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  return (
    <Box>
      <Heading size="md" mb={4}>Teachers</Heading>
      {tempPassword && (
        <Box bg="yellow.50" borderWidth="1px" borderColor="yellow.200" rounded="md" p={3} mb={4}>
          <Text fontWeight="bold">Temporary password for the newly created teacher:</Text>
          <Text fontFamily="mono">{tempPassword}</Text>
          <Text mt={2} color="gray.600">Please ask them to sign in and change it immediately.</Text>
        </Box>
      )}

      {/* Create form */}
      <Box bg="white" borderWidth="1px" rounded="md" p={4} mb={4}>
        <VStack align="stretch" spacing={3}>
          <HStack>
            <FormControl isRequired>
              <FormLabel>Email</FormLabel>
              <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>Full name</FormLabel>
              <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            </FormControl>
          </HStack>
          <HStack>
            <FormControl>
              <FormLabel>Phone</FormLabel>
              <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </FormControl>
            <FormControl>
              <FormLabel>Address</FormLabel>
              <Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
            </FormControl>
          </HStack>
          <HStack>
            <FormControl>
              <FormLabel>Qualification</FormLabel>
              <Input value={form.qualification} onChange={(e) => setForm({ ...form, qualification: e.target.value })} />
            </FormControl>
            <FormControl>
              <FormLabel>Specialization</FormLabel>
              <Input value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} />
            </FormControl>
            <FormControl>
              <FormLabel>Salary</FormLabel>
              <Input value={form.salary} onChange={(e) => setForm({ ...form, salary: e.target.value })} />
            </FormControl>
          </HStack>
          <HStack justify="flex-end">
            <Button colorScheme="brand" onClick={createTeacher}>Add Teacher</Button>
          </HStack>
        </VStack>
      </Box>

      <Box bg="white" borderWidth="1px" rounded="md" p={4} mt={4}>
        <Heading size="sm" mb={3}>Assign Teacher to Class & Subject</Heading>
        <VStack align="stretch" spacing={3}>
          <HStack>
            <FormControl isRequired>
              <FormLabel>Teacher</FormLabel>
              <Input placeholder="Teacher ID" value={assignment.teacher_id} onChange={(e) => setAssignment({ ...assignment, teacher_id: e.target.value })} />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>Class</FormLabel>
              <Input list="classes" value={assignment.class_id} onChange={(e) => setAssignment({ ...assignment, class_id: e.target.value })} />
              <datalist id="classes">
                {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </datalist>
            </FormControl>
            <FormControl isRequired>
              <FormLabel>Subject</FormLabel>
              <Input list="subjects" value={assignment.subject_id} onChange={(e) => setAssignment({ ...assignment, subject_id: e.target.value })} />
              <datalist id="subjects">
                {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </datalist>
            </FormControl>
          </HStack>
          <HStack>
            <FormControl isRequired>
              <FormLabel>Academic Year</FormLabel>
              <Input placeholder="e.g. 2025" value={assignment.academic_year} onChange={(e) => setAssignment({ ...assignment, academic_year: e.target.value })} />
            </FormControl>
            <FormControl display="flex" alignItems="center">
              <FormLabel mb={0}>Primary</FormLabel>
              <Switch isChecked={assignment.is_primary} onChange={(e) => setAssignment({ ...assignment, is_primary: e.target.checked })} />
            </FormControl>
            <HStack justify="flex-end" flex="1">
              <Button onClick={async () => {
                try {
                  await api.post('/teachers/assignments', {
                    teacher_id: Number(assignment.teacher_id),
                    class_id: Number(assignment.class_id),
                    subject_id: Number(assignment.subject_id),
                    academic_year: assignment.academic_year || new Date().getFullYear().toString(),
                    is_primary: assignment.is_primary,
                  })
                  toast({ title: 'Assignment added', status: 'success' })
                } catch (e:any) {
                  toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
                }
              }} colorScheme="brand">Assign</Button>
            </HStack>
          </HStack>
        </VStack>
      </Box>

      {/* Search and table */}
      <Box bg="white" borderWidth="1px" rounded="md" p={4}>
        <HStack mb={3}>
          <InputGroup maxW="360px">
            <InputLeftElement>
              <Icon as={SearchIcon} color="gray.400" />
            </InputLeftElement>
            <Input placeholder="Search by name or email" value={query} onChange={(e) => setQuery(e.target.value)} />
          </InputGroup>
        </HStack>
        <Table size="sm" variant="simple">
          <Thead>
            <Tr>
              <Th>Name</Th>
              <Th>Email</Th>
              <Th>Active</Th>
              <Th></Th>
            </Tr>
          </Thead>
          <Tbody>
            {filtered.map(t => (
              <Tr key={t.id}>
                <Td>{t.full_name}</Td>
                <Td>{t.email}</Td>
                <Td><Switch isChecked={t.is_active} onChange={() => toggleActive(t)} /></Td>
                <Td isNumeric>
                  <IconButton aria-label="Edit" size="sm" icon={<EditIcon />} onClick={() => setEditing(t)} />
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>

      {/* Edit panel */}
      {editing && (
        <Box bg="white" borderWidth="1px" rounded="md" p={4} mt={4}>
          <Heading size="sm" mb={3}>Edit Teacher</Heading>
          <VStack align="stretch" spacing={3}>
            <HStack>
              <FormControl>
                <FormLabel>Full name</FormLabel>
                <Input value={editing.full_name} onChange={(e) => setEditing({ ...editing, full_name: e.target.value })} />
              </FormControl>
              <FormControl>
                <FormLabel>Phone</FormLabel>
                <Input value={editing.phone || ''} onChange={(e) => setEditing({ ...editing, phone: e.target.value })} />
              </FormControl>
              <FormControl>
                <FormLabel>Address</FormLabel>
                <Input value={editing.address || ''} onChange={(e) => setEditing({ ...editing, address: e.target.value })} />
              </FormControl>
            </HStack>
            <HStack>
              <FormControl>
                <FormLabel>Qualification</FormLabel>
                <Input value={editing.qualification || ''} onChange={(e) => setEditing({ ...editing, qualification: e.target.value })} />
              </FormControl>
              <FormControl>
                <FormLabel>Specialization</FormLabel>
                <Input value={editing.specialization || ''} onChange={(e) => setEditing({ ...editing, specialization: e.target.value })} />
              </FormControl>
              <FormControl>
                <FormLabel>Salary</FormLabel>
                <Input value={editing.salary?.toString() || ''} onChange={(e) => setEditing({ ...editing, salary: Number(e.target.value) })} />
              </FormControl>
            </HStack>
            <HStack justify="flex-end">
              <Button onClick={() => setEditing(null)} variant="ghost">Cancel</Button>
              <Button colorScheme="brand" onClick={saveEdit}>Save</Button>
            </HStack>
          </VStack>
        </Box>
      )}
    </Box>
  )
}


