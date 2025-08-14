import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { Box, Heading, Text, SimpleGrid, Table, Thead, Tr, Th, Tbody, Td, Divider, HStack, Button, useToast, Spinner, Alert, AlertIcon } from '@chakra-ui/react'

export default function StudentDetailsPage() {
  const { id } = useParams()
  const { user, isLoading: authLoading } = useAuth()
  const toast = useToast()
  const [student, setStudent] = useState<any>(null)
  const [records, setRecords] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    if (!user) return
    setLoading(true)
    try {
      const st = await api.get(`/students/${id}`)
      const rec = await api.get('/academic/academic-records', { params: { student_id: Number(id) } })
      setStudent(st.data)
      setRecords(rec.data)
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user && !authLoading) {
      load()
    }
  }, [id, user, authLoading])

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
          Please log in to view student details.
        </Alert>
      </Box>
    )
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minH="200px">
        <Spinner size="lg" />
      </Box>
    )
  }

  if (!student) {
    return (
      <Box>
        <Alert status="info">
          <AlertIcon />
          Student not found.
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      <Heading size="md" mb={2}>{student.first_name} {student.last_name}</Heading>
      <Text color="gray.600" mb={4}>Student ID: {student.student_number || '-'} • Admission: {student.admission_no} • Class: {student.current_class || '-'}</Text>
      <Divider mb={4} />

      <Heading size="sm" mb={2}>Academic History</Heading>
      <Table size="sm" variant="simple">
        <Thead>
          <Tr>
            <Th>Term</Th>
            <Th>Year</Th>
            <Th>Subject</Th>
            <Th>CA</Th>
            <Th>Exam</Th>
            <Th>Overall</Th>
            <Th>Grade</Th>
          </Tr>
        </Thead>
        <Tbody>
          {records.map((r, idx) => (
            <Tr key={idx}>
              <Td>{r.term}</Td>
              <Td>{r.academic_year}</Td>
              <Td>{r.subject_name}</Td>
              <Td>{r.ca_score ?? '-'}</Td>
              <Td>{r.exam_score ?? '-'}</Td>
              <Td>{r.overall_score ?? '-'}</Td>
              <Td>{r.grade ?? '-'}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  )
}



