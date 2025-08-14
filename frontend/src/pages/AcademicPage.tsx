import { useEffect, useState } from 'react'
import { Box, Heading, Text, SimpleGrid, Input, Button, HStack, useToast, VStack, Select, Divider, FormControl, FormLabel, Card, CardHeader, CardBody, InputGroup, InputLeftElement, Icon, Table, Thead, Tr, Th, Tbody, Td } from '@chakra-ui/react'
import { SearchIcon } from '@chakra-ui/icons'
import jsPDF from 'jspdf'
import 'jspdf-autotable'
import { api } from '../lib/api'
import { useLocation } from 'react-router-dom'

export default function AcademicPage() {
  const toast = useToast()
  const location = useLocation()
  const [classes, setClasses] = useState<any[]>([])
  const [subjects, setSubjects] = useState<any[]>([])
  const [students, setStudents] = useState<any[]>([])
  const [classForm, setClassForm] = useState({ name: '', grade_level: '', capacity: 40, academic_year: '' })
  const [subjectForm, setSubjectForm] = useState({ name: '', code: '', description: '' })
  const [recordForm, setRecordForm] = useState({ student_id: '', subject_id: '', class_id: '', term: '', year: '', ca_score: '', exam_score: '' })
  const [recordQuery, setRecordQuery] = useState('')
  const [records, setRecords] = useState<any[]>([])
  const [reportForm, setReportForm] = useState({ student_id: '', term: '', year: '' })
  const [report, setReport] = useState<any | null>(null)

  const load = async () => {
    try {
      const [c, s, st] = await Promise.all([
        api.get('/academic/classes').catch(() => ({ data: [] })),
        api.get('/academic/subjects').catch(() => ({ data: [] })),
        api.get('/students').catch(() => ({ data: [] })),
      ])
      setClasses(c.data)
      setSubjects(s.data)
      setStudents(st.data)
    } catch {}
  }

  useEffect(() => { load() }, [])

  // Prefill from URL params (e.g., /academic?class_id=1&subject_id=2)
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const cid = params.get('class_id') || ''
    const sid = params.get('subject_id') || ''
    const term = params.get('term') || ''
    const year = params.get('year') || ''
    setRecordForm((f) => ({ ...f, class_id: cid, subject_id: sid, term, year }))
  }, [location.search])

  const createClass = async () => {
    if (!classForm.name) return toast({ title: 'Name is required', status: 'warning' })
    try {
      await api.post('/academic/classes', {
        name: classForm.name,
        grade_level: classForm.grade_level || null,
        capacity: Number(classForm.capacity) || 40,
        academic_year: classForm.academic_year || new Date().getFullYear().toString()
      })
      setClassForm({ name: '', grade_level: '', capacity: 40, academic_year: '' })
      await load()
      toast({ title: 'Class created', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  const createSubject = async () => {
    if (!subjectForm.name || !subjectForm.code) return toast({ title: 'Name and code are required', status: 'warning' })
    try {
      await api.post('/academic/subjects', subjectForm)
      setSubjectForm({ name: '', code: '', description: '' })
      await load()
      toast({ title: 'Subject created', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  const recordResult = async () => {
    if (!recordForm.student_id || !recordForm.subject_id || !recordForm.class_id || !recordForm.term) {
      return toast({ title: 'Please fill student, subject, class and term', status: 'warning' })
    }
    try {
      await api.post('/academic/academic-records', {
        student_id: Number(recordForm.student_id),
        subject_id: Number(recordForm.subject_id),
        class_id: Number(recordForm.class_id),
        term: recordForm.term,
        academic_year: recordForm.year || new Date().getFullYear().toString(),
        ca_score: recordForm.ca_score ? Number(recordForm.ca_score) : null,
        exam_score: recordForm.exam_score ? Number(recordForm.exam_score) : null,
      })
      setRecordForm({ student_id: '', subject_id: '', class_id: '', term: '', year: '', ca_score: '', exam_score: '' })
      toast({ title: 'Result recorded', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  const generateReport = async () => {
    if (!reportForm.student_id || !reportForm.term) return toast({ title: 'Student and term required', status: 'warning' })
    try {
      const res = await api.get('/academic/report-card/' + reportForm.student_id, {
        params: { term: reportForm.term, academic_year: reportForm.year || new Date().getFullYear().toString() }
      })
      setReport(res.data)
    } catch (e: any) {
      setReport(null)
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  const exportPDF = () => {
    if (!report) return
    const doc = new jsPDF()
    doc.setFontSize(14)
    doc.text(`${report.student.name} - ${report.student.class || ''}`, 14, 18)
    doc.setFontSize(11)
    doc.text(`${report.term} ${report.academic_year}`, 14, 26)
    // @ts-ignore
    doc.autoTable({
      head: [['Subject', 'CA', 'Exam', 'Overall', 'Grade']],
      body: report.subjects.map((r: any) => [r.subject_name, r.ca_score ?? '-', r.exam_score ?? '-', r.overall_score ?? '-', r.grade ?? '-']),
      startY: 32
    })
    doc.text(`Average: ${report.overall_average ?? '-'}`, 14, (doc as any).lastAutoTable.finalY + 10)
    doc.save(`report-card-${report.student.name.replace(/\s+/g, '-')}-${report.term}-${report.academic_year}.pdf`)
  }

  const loadRecords = async () => {
    try {
      const params: any = {}
      if (recordForm.student_id) params.student_id = Number(recordForm.student_id)
      if (recordForm.class_id) params.class_id = Number(recordForm.class_id)
      if (recordForm.subject_id) params.subject_id = Number(recordForm.subject_id)
      const res = await api.get('/academic/academic-records', { params })
      setRecords(res.data)
    } catch {}
  }

  return (
    <Box>
      <Heading size="md" mb={4}>Academic</Heading>

      <SimpleGrid columns={[1, 2]} spacing={4} mb={6}>
        <Card>
          <CardHeader><Heading size="sm">Create Class</Heading></CardHeader>
          <CardBody>
            <VStack spacing={3} align="stretch">
              <HStack>
                <FormControl isRequired>
                  <FormLabel>Name</FormLabel>
                  <Input placeholder="e.g. Form 1" value={classForm.name} onChange={(e) => setClassForm({ ...classForm, name: e.target.value })} />
                </FormControl>
                <FormControl>
                  <FormLabel>Grade Level</FormLabel>
                  <Input placeholder="e.g. 9" value={classForm.grade_level} onChange={(e) => setClassForm({ ...classForm, grade_level: e.target.value })} />
                </FormControl>
              </HStack>
              <HStack>
                <FormControl>
                  <FormLabel>Capacity</FormLabel>
                  <Input type="number" value={classForm.capacity} onChange={(e) => setClassForm({ ...classForm, capacity: Number(e.target.value) })} />
                </FormControl>
                <FormControl>
                  <FormLabel>Academic Year</FormLabel>
                  <Input placeholder="e.g. 2025" value={classForm.academic_year} onChange={(e) => setClassForm({ ...classForm, academic_year: e.target.value })} />
                </FormControl>
              </HStack>
              <HStack justify="flex-end"><Button colorScheme="brand" onClick={createClass}>Add Class</Button></HStack>
            </VStack>
          </CardBody>
        </Card>

        <Card>
          <CardHeader><Heading size="sm">Create Subject</Heading></CardHeader>
          <CardBody>
            <VStack spacing={3} align="stretch">
              <HStack>
                <FormControl isRequired>
                  <FormLabel>Name</FormLabel>
                  <Input value={subjectForm.name} onChange={(e) => setSubjectForm({ ...subjectForm, name: e.target.value })} />
                </FormControl>
                <FormControl isRequired>
                  <FormLabel>Code</FormLabel>
                  <Input value={subjectForm.code} onChange={(e) => setSubjectForm({ ...subjectForm, code: e.target.value })} />
                </FormControl>
              </HStack>
              <FormControl>
                <FormLabel>Description</FormLabel>
                <Input value={subjectForm.description} onChange={(e) => setSubjectForm({ ...subjectForm, description: e.target.value })} />
              </FormControl>
              <HStack justify="flex-end"><Button colorScheme="brand" onClick={createSubject}>Add Subject</Button></HStack>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      <SimpleGrid columns={[1, 2]} spacing={4} mb={6}>
        <Card>
          <CardHeader><Heading size="sm">Classes</Heading></CardHeader>
          <CardBody>
            <SimpleGrid columns={[1, 2, 3]} spacing={3}>
              {classes.map((c) => (
                <Box key={c.id} borderWidth="1px" rounded="md" p={3}>
                  <Text fontWeight="bold">{c.name}</Text>
                  <Text color="gray.600">Year: {c.academic_year}</Text>
                  <Text color="gray.600">Capacity: {c.capacity}</Text>
                </Box>
              ))}
            </SimpleGrid>
          </CardBody>
        </Card>

        <Card>
          <CardHeader><Heading size="sm">Subjects</Heading></CardHeader>
          <CardBody>
            <SimpleGrid columns={[1, 2, 3]} spacing={3}>
              {subjects.map((s) => (
                <Box key={s.id} borderWidth="1px" rounded="md" p={3}>
                  <Text fontWeight="bold">{s.name} ({s.code})</Text>
                  <Text color="gray.600">{s.description || '-'}</Text>
                </Box>
              ))}
            </SimpleGrid>
          </CardBody>
        </Card>
      </SimpleGrid>

      <Card mb={6}>
        <CardHeader><Heading size="sm">Record Examination/CA Scores</Heading></CardHeader>
        <CardBody>
          <VStack align="stretch" spacing={3}>
            <HStack>
              <FormControl isRequired>
                <FormLabel>Student</FormLabel>
                <Select placeholder="Select" value={recordForm.student_id} onChange={(e) => setRecordForm({ ...recordForm, student_id: e.target.value })}>
                  {students.map(st => (
                    <option key={st.id} value={st.id}>{st.first_name} {st.last_name} {st.student_number ? `(${st.student_number})` : ''}</option>
                  ))}
                </Select>
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Subject</FormLabel>
                <Select placeholder="Select" value={recordForm.subject_id} onChange={(e) => setRecordForm({ ...recordForm, subject_id: e.target.value })}>
                  {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </Select>
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Class</FormLabel>
                <Select placeholder="Select" value={recordForm.class_id} onChange={(e) => setRecordForm({ ...recordForm, class_id: e.target.value })}>
                  {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </Select>
              </FormControl>
            </HStack>
            <HStack>
              <FormControl isRequired>
                <FormLabel>Term</FormLabel>
                <Input placeholder="e.g. Term 1" value={recordForm.term} onChange={(e) => setRecordForm({ ...recordForm, term: e.target.value })} />
              </FormControl>
              <FormControl>
                <FormLabel>Academic Year</FormLabel>
                <Input placeholder="e.g. 2025" value={recordForm.year} onChange={(e) => setRecordForm({ ...recordForm, year: e.target.value })} />
              </FormControl>
              <FormControl>
                <FormLabel>CA Score</FormLabel>
                <Input placeholder="e.g. 30" value={recordForm.ca_score} onChange={(e) => setRecordForm({ ...recordForm, ca_score: e.target.value })} />
              </FormControl>
              <FormControl>
                <FormLabel>Exam Score</FormLabel>
                <Input placeholder="e.g. 70" value={recordForm.exam_score} onChange={(e) => setRecordForm({ ...recordForm, exam_score: e.target.value })} />
              </FormControl>
              <Button colorScheme="brand" onClick={recordResult}>Save Result</Button>
            </HStack>
            <HStack justify="space-between" mt={2}>
              <Button variant="outline" onClick={loadRecords}>Load Existing Records</Button>
              <InputGroup maxW="320px">
                <InputLeftElement>
                  <Icon as={SearchIcon} color="gray.400" />
                </InputLeftElement>
                <Input placeholder="Filter by subject or term" value={recordQuery} onChange={(e) => setRecordQuery(e.target.value)} />
              </InputGroup>
            </HStack>
            {records.length > 0 && (
              <Box borderWidth="1px" rounded="md" p={3}>
                <Table size="sm" variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Student</Th>
                      <Th>Subject</Th>
                      <Th>Class</Th>
                      <Th>Term</Th>
                      <Th>CA</Th>
                      <Th>Exam</Th>
                      <Th>Overall</Th>
                      <Th>Grade</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {records.filter((r) => {
                      const q = recordQuery.trim().toLowerCase()
                      if (!q) return true
                      return (
                        (r.subject_name || '').toLowerCase().includes(q) ||
                        (r.term || '').toLowerCase().includes(q)
                      )
                    }).map((r, idx) => (
                      <Tr key={idx}>
                        <Td>{r.student_name}</Td>
                        <Td>{r.subject_name}</Td>
                        <Td>{r.class_name}</Td>
                        <Td>{r.term} {r.academic_year}</Td>
                        <Td>{r.ca_score ?? '-'}</Td>
                        <Td>{r.exam_score ?? '-'}</Td>
                        <Td>{r.overall_score ?? '-'}</Td>
                        <Td>{r.grade ?? '-'}</Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
            )}
          </VStack>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><Heading size="sm">Student Report Card</Heading></CardHeader>
        <CardBody>
          <HStack spacing={2} mb={3}>
            <FormControl isRequired>
              <FormLabel>Student</FormLabel>
              <Select placeholder="Select" value={reportForm.student_id} onChange={(e) => setReportForm({ ...reportForm, student_id: e.target.value })}>
                {students.map(st => (
                  <option key={st.id} value={st.id}>{st.first_name} {st.last_name} {st.student_number ? `(${st.student_number})` : ''}</option>
                ))}
              </Select>
            </FormControl>
            <FormControl isRequired>
              <FormLabel>Term</FormLabel>
              <Input placeholder="e.g. Term 1" value={reportForm.term} onChange={(e) => setReportForm({ ...reportForm, term: e.target.value })} />
            </FormControl>
            <FormControl>
              <FormLabel>Academic Year</FormLabel>
              <Input placeholder="e.g. 2025" value={reportForm.year} onChange={(e) => setReportForm({ ...reportForm, year: e.target.value })} />
            </FormControl>
            <Button onClick={generateReport}>Generate</Button>
          </HStack>
          {report && (
            <Box borderWidth="1px" rounded="md" p={4} bg="gray.50">
              <Heading size="sm" mb={2}>{report.student.name} - {report.student.class}</Heading>
              <Text color="gray.600" mb={3}>{report.term} {report.academic_year}</Text>
              <HStack mb={3}><Button size="sm" onClick={exportPDF}>Export PDF</Button></HStack>
              <SimpleGrid columns={[1, 2, 3]} spacing={3}>
                {report.subjects.map((r: any, idx: number) => (
                  <Box key={idx} borderWidth="1px" rounded="md" p={3} bg="white">
                    <Text fontWeight="bold">{r.subject_name} ({r.subject_code})</Text>
                    <Text>CA: {r.ca_score ?? '-'}</Text>
                    <Text>Exam: {r.exam_score ?? '-'}</Text>
                    <Text>Overall: {r.overall_score ?? '-'}</Text>
                    <Text>Grade: {r.grade ?? '-'}</Text>
                  </Box>
                ))}
              </SimpleGrid>
              <Text mt={3} fontWeight="bold">Average: {report.overall_average ?? '-'}</Text>
            </Box>
          )}
        </CardBody>
      </Card>
    </Box>
  )
}


