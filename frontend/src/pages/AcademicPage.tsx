import React, { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  SimpleGrid,
  Input,
  Button,
  HStack,
  VStack,
  useToast,
  Select,
  Divider,
  FormControl,
  FormLabel,
  Card,
  CardHeader,
  CardBody,
  InputGroup,
  InputLeftElement,
  Icon,
  Table,
  Thead,
  Tr,
  Th,
  Tbody,
  Td,
  Badge,
  Spinner,
  useColorModeValue,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Grid,
  GridItem,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Textarea,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Switch,
  Alert,
  AlertIcon,
  IconButton,
  Tooltip,
  Flex,
  Spacer,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink
} from '@chakra-ui/react'
import { 
  SearchIcon, 
  AddIcon, 
  EditIcon, 
  DeleteIcon, 
  ViewIcon,
  DownloadIcon,
  CalendarIcon,
  TimeIcon,
  CheckCircleIcon,
  WarningIcon,
  InfoIcon,
  ChevronRightIcon
} from '@chakra-ui/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import jsPDF from 'jspdf'
import 'jspdf-autotable'

interface Class {
  id: number
  name: string
  grade_level: string
  capacity: number
  academic_year: string
  teacher_id?: number
  teacher_name?: string
}

interface Subject {
  id: number
  name: string
  code: string
  description: string
  credits: number
}

interface Student {
  id: number
  first_name: string
  last_name: string
  admission_no: string
  current_class: string
  parent_phone: string
}

interface AcademicRecord {
  id: number
  student_id: number
  subject_id: number
  class_id: number
  term: string
  academic_year: string
  ca_score: number
  exam_score: number
  overall_score: number
  grade: string
  remarks: string
  student_name: string
  subject_name: string
  class_name: string
}

interface Attendance {
  id: number
  student_id: number
  class_id: number
  date: string
  status: 'present' | 'absent' | 'late' | 'excused'
  notes: string
  student_name: string
  class_name: string
}

interface ExamSchedule {
  id: number
  title: string
  subject_id: number
  class_id: number
  exam_date: string
  start_time: string
  duration: number
  total_marks: number
  subject_name: string
  class_name: string
}

export default function AcademicPage() {
  const toast = useToast()
  const location = useLocation()
  const navigate = useNavigate()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const { isOpen: isExamOpen, onOpen: onExamOpen, onClose: onExamClose } = useDisclosure()
  const { isOpen: isAttendanceOpen, onOpen: onAttendanceOpen, onClose: onAttendanceClose } = useDisclosure()
  
  // State variables
  const [activeTab, setActiveTab] = useState('overview')
  const [classes, setClasses] = useState<Class[]>([])
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [students, setStudents] = useState<Student[]>([])
  const [records, setRecords] = useState<AcademicRecord[]>([])
  const [attendance, setAttendance] = useState<Attendance[]>([])
  const [examSchedules, setExamSchedules] = useState<ExamSchedule[]>([])
  const [isLoading, setIsLoading] = useState(true)
  
  // Form states
  const [classForm, setClassForm] = useState({ name: '', grade_level: '', capacity: 40, academic_year: '' })
  const [subjectForm, setSubjectForm] = useState({ name: '', code: '', description: '', credits: 1 })
  const [recordForm, setRecordForm] = useState({ 
    student_id: '', subject_id: '', class_id: '', term: '', year: '', 
    ca_score: '', exam_score: '', remarks: '' 
  })
  const [examForm, setExamForm] = useState({
    title: '', subject_id: '', class_id: '', exam_date: '', start_time: '', duration: 60, total_marks: 100
  })
  const [attendanceForm, setAttendanceForm] = useState({
    class_id: '', date: '', bulk_records: [] as Array<{student_id: number, status: string, notes: string}>
  })
  
  // Filter states
  const [recordQuery, setRecordQuery] = useState('')
  const [reportForm, setReportForm] = useState({ student_id: '', term: '', year: '' })
  const [report, setReport] = useState<any | null>(null)
  
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  useEffect(() => {
    loadData()
  }, [])

  // Prefill from URL params
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const cid = params.get('class_id') || ''
    const sid = params.get('subject_id') || ''
    const term = params.get('term') || ''
    const year = params.get('year') || ''
    setRecordForm((f) => ({ ...f, class_id: cid, subject_id: sid, term, year }))
  }, [location.search])

  const loadData = async () => {
    try {
      setIsLoading(true)
      const [c, s, st, r, a, e] = await Promise.all([
        api.get('/academic/classes').catch(() => ({ data: [] })),
        api.get('/academic/subjects').catch(() => ({ data: [] })),
        api.get('/students').catch(() => ({ data: [] })),
        api.get('/academic/academic-records').catch(() => ({ data: [] })),
        api.get('/academic/attendance').catch(() => ({ data: [] })),
        api.get('/academic/exam-schedules').catch(() => ({ data: [] }))
      ])
      setClasses(c.data)
      setSubjects(s.data)
      setStudents(st.data)
      setRecords(r.data)
      setAttendance(a.data)
      setExamSchedules(e.data)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Class Management
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
      await loadData()
      toast({ title: 'Class created', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  // Subject Management
  const createSubject = async () => {
    if (!subjectForm.name || !subjectForm.code) return toast({ title: 'Name and code are required', status: 'warning' })
    try {
      await api.post('/academic/subjects', subjectForm)
      setSubjectForm({ name: '', code: '', description: '', credits: 1 })
      await loadData()
      toast({ title: 'Subject created', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  // Academic Records
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
        remarks: recordForm.remarks
      })
      setRecordForm({ student_id: '', subject_id: '', class_id: '', term: '', year: '', ca_score: '', exam_score: '', remarks: '' })
      await loadData()
      toast({ title: 'Result recorded', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  // Exam Scheduling
  const createExam = async () => {
    if (!examForm.title || !examForm.subject_id || !examForm.class_id || !examForm.exam_date) {
      return toast({ title: 'Please fill all required fields', status: 'warning' })
    }
    try {
      await api.post('/academic/exam-schedules', examForm)
      setExamForm({ title: '', subject_id: '', class_id: '', exam_date: '', start_time: '', duration: 60, total_marks: 100 })
      await loadData()
      toast({ title: 'Exam scheduled', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  // Bulk Attendance
  const openBulkAttendance = (classId: number) => {
    const classStudents = students.filter(s => s.current_class === classes.find(c => c.id === classId)?.name)
    setAttendanceForm({
      class_id: classId.toString(),
      date: new Date().toISOString().split('T')[0],
      bulk_records: classStudents.map(s => ({ student_id: s.id, status: 'present', notes: '' }))
    })
    onAttendanceOpen()
  }

  const saveBulkAttendance = async () => {
    try {
      await api.post('/academic/attendance/bulk', {
        class_id: Number(attendanceForm.class_id),
        date: attendanceForm.date,
        attendance_records: attendanceForm.bulk_records
      })
      onAttendanceClose()
      await loadData()
      toast({ title: 'Attendance recorded', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  // Report Generation
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

  if (isLoading) {
    return (
      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="center">
          <Spinner size="xl" />
          <Text>Loading academic data...</Text>
        </VStack>
      </Container>
    )
  }

  return (
    <Box>
      {/* Breadcrumb */}
      <Box bg={bgColor} borderBottom="1px" borderColor={borderColor} py={2}>
        <Container maxW="container.xl">
          <Breadcrumb spacing="8px" separator={<ChevronRightIcon color="gray.500" />}>
            <BreadcrumbItem>
              <BreadcrumbLink href="/app">Dashboard</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem isCurrentPage>
              <BreadcrumbLink>Academic Management</BreadcrumbLink>
            </BreadcrumbItem>
          </Breadcrumb>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="stretch">
          {/* Header */}
          <Box>
            <Heading size="lg" mb={2}>Academic Management</Heading>
            <Text color="gray.600">Comprehensive academic administration and student performance tracking</Text>
          </Box>

          {/* Quick Stats */}
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Total Classes</StatLabel>
                  <StatNumber>{classes.length}</StatNumber>
                  <StatHelpText>Active academic year</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Total Subjects</StatLabel>
                  <StatNumber>{subjects.length}</StatNumber>
                  <StatHelpText>Available courses</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Total Students</StatLabel>
                  <StatNumber>{students.length}</StatNumber>
                  <StatHelpText>Enrolled learners</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Exam Schedules</StatLabel>
                  <StatNumber>{examSchedules.length}</StatNumber>
                  <StatHelpText>Upcoming tests</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </SimpleGrid>

          {/* Main Content Tabs */}
          <Tabs value={activeTab} onChange={setActiveTab} variant="enclosed">
            <TabList>
              <Tab>Overview</Tab>
              <Tab>Classes & Subjects</Tab>
              <Tab>Academic Records</Tab>
              <Tab>Attendance</Tab>
              <Tab>Exam Schedule</Tab>
              <Tab>Reports</Tab>
            </TabList>

            <TabPanels>
              {/* Overview Tab */}
              <TabPanel>
                <VStack spacing={6} align="stretch">
                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    <Card>
                      <CardHeader>
                        <Heading size="sm">Recent Academic Records</Heading>
                      </CardHeader>
                      <CardBody>
                        <VStack align="stretch" spacing={3}>
                          {records.slice(0, 5).map((record, idx) => (
                            <HStack key={idx} justify="space-between" p={3} bg="gray.50" rounded="md">
                              <VStack align="start" spacing={1}>
                                <Text fontWeight="medium">{record.student_name}</Text>
                                <Text fontSize="sm" color="gray.600">
                                  {record.subject_name} - {record.term}
                                </Text>
                              </VStack>
                              <Badge colorScheme={record.overall_score >= 50 ? "green" : "red"}>
                                {record.overall_score || 'N/A'}
                              </Badge>
                            </HStack>
                          ))}
                        </VStack>
                      </CardBody>
                    </Card>

                    <Card>
                      <CardHeader>
                        <Heading size="sm">Upcoming Exams</Heading>
                      </CardHeader>
                      <CardBody>
                        <VStack align="stretch" spacing={3}>
                          {examSchedules.slice(0, 5).map((exam, idx) => (
                            <HStack key={idx} justify="space-between" p={3} bg="gray.50" rounded="md">
                              <VStack align="start" spacing={1}>
                                <Text fontWeight="medium">{exam.title}</Text>
                                <Text fontSize="sm" color="gray.600">
                                  {exam.subject_name} - {exam.class_name}
                                </Text>
                              </VStack>
                              <Text fontSize="sm" color="gray.600">
                                {new Date(exam.exam_date).toLocaleDateString()}
                              </Text>
                            </HStack>
                          ))}
                        </VStack>
                      </CardBody>
                    </Card>
                  </SimpleGrid>
                </VStack>
              </TabPanel>

              {/* Classes & Subjects Tab */}
              <TabPanel>
                <VStack spacing={6} align="stretch">
                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    <Card>
                      <CardHeader>
                        <Heading size="sm">Create Class</Heading>
                      </CardHeader>
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
                              <NumberInput value={classForm.capacity} onChange={(_, value) => setClassForm({ ...classForm, capacity: value })} min={1} max={100}>
                                <NumberInputField />
                                <NumberInputStepper>
                                  <NumberIncrementStepper />
                                  <NumberDecrementStepper />
                                </NumberInputStepper>
                              </NumberInput>
                            </FormControl>
                            <FormControl>
                              <FormLabel>Academic Year</FormLabel>
                              <Input placeholder="e.g. 2025" value={classForm.academic_year} onChange={(e) => setClassForm({ ...classForm, academic_year: e.target.value })} />
                            </FormControl>
                          </HStack>
                          <Button colorScheme="blue" onClick={createClass}>Add Class</Button>
                        </VStack>
                      </CardBody>
                    </Card>

                    <Card>
                      <CardHeader>
                        <Heading size="sm">Create Subject</Heading>
                      </CardHeader>
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
                            <Textarea value={subjectForm.description} onChange={(e) => setSubjectForm({ ...subjectForm, description: e.target.value })} />
                          </FormControl>
                          <FormControl>
                            <FormLabel>Credits</FormLabel>
                            <NumberInput value={subjectForm.credits} onChange={(_, value) => setSubjectForm({ ...subjectForm, credits: value })} min={1} max={10}>
                              <NumberInputField />
                              <NumberInputStepper>
                                <NumberIncrementStepper />
                                <NumberDecrementStepper />
                              </NumberInputStepper>
                            </NumberInput>
                          </FormControl>
                          <Button colorScheme="blue" onClick={createSubject}>Add Subject</Button>
                        </VStack>
                      </CardBody>
                    </Card>
                  </SimpleGrid>

                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    <Card>
                      <CardHeader>
                        <Heading size="sm">Classes</Heading>
                      </CardHeader>
                      <CardBody>
                        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                          {classes.map((c) => (
                            <Box key={c.id} borderWidth="1px" rounded="md" p={3}>
                              <Text fontWeight="bold">{c.name}</Text>
                              <Text color="gray.600">Year: {c.academic_year}</Text>
                              <Text color="gray.600">Capacity: {c.capacity}</Text>
                              {c.teacher_name && <Text color="gray.600">Teacher: {c.teacher_name}</Text>}
                            </Box>
                          ))}
                        </SimpleGrid>
                      </CardBody>
                    </Card>

                    <Card>
                      <CardHeader>
                        <Heading size="sm">Subjects</Heading>
                      </CardHeader>
                      <CardBody>
                        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                          {subjects.map((s) => (
                            <Box key={s.id} borderWidth="1px" rounded="md" p={3}>
                              <Text fontWeight="bold">{s.name} ({s.code})</Text>
                              <Text color="gray.600">{s.description || '-'}</Text>
                              <Text color="gray.600">Credits: {s.credits}</Text>
                            </Box>
                          ))}
                        </SimpleGrid>
                      </CardBody>
                    </Card>
                  </SimpleGrid>
                </VStack>
              </TabPanel>

              {/* Academic Records Tab */}
              <TabPanel>
                <VStack spacing={6} align="stretch">
                  <Card>
                    <CardHeader>
                      <Heading size="sm">Record Examination/CA Scores</Heading>
                    </CardHeader>
                    <CardBody>
                      <VStack align="stretch" spacing={3}>
                        <HStack>
                          <FormControl isRequired>
                            <FormLabel>Student</FormLabel>
                            <Select placeholder="Select" value={recordForm.student_id} onChange={(e) => setRecordForm({ ...recordForm, student_id: e.target.value })}>
                              {students.map(st => (
                                <option key={st.id} value={st.id}>{st.first_name} {st.last_name} {st.admission_no ? `(${st.admission_no})` : ''}</option>
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
                            <NumberInput value={recordForm.ca_score} onChange={(_, value) => setRecordForm({ ...recordForm, ca_score: value.toString() })} min={0} max={100}>
                              <NumberInputField />
                            </NumberInput>
                          </FormControl>
                          <FormControl>
                            <FormLabel>Exam Score</FormLabel>
                            <NumberInput value={recordForm.exam_score} onChange={(_, value) => setRecordForm({ ...recordForm, exam_score: value.toString() })} min={0} max={100}>
                              <NumberInputField />
                            </NumberInput>
                          </FormControl>
                        </HStack>
                        <FormControl>
                          <FormLabel>Remarks</FormLabel>
                          <Textarea value={recordForm.remarks} onChange={(e) => setRecordForm({ ...recordForm, remarks: e.target.value })} placeholder="Additional comments..." />
                        </FormControl>
                        <HStack justify="space-between">
                          <Button colorScheme="blue" onClick={recordResult}>Save Result</Button>
                          <Button variant="outline" onClick={loadRecords}>Load Existing Records</Button>
                        </HStack>
                        
                        {records.length > 0 && (
                          <Box>
                            <InputGroup maxW="320px" mb={3}>
                              <InputLeftElement>
                                <Icon as={SearchIcon} color="gray.400" />
                              </InputLeftElement>
                              <Input placeholder="Filter by subject or term" value={recordQuery} onChange={(e) => setRecordQuery(e.target.value)} />
                            </InputGroup>
                            <Box borderWidth="1px" rounded="md" p={3} maxH="400px" overflowY="auto">
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
                          </Box>
                        )}
                      </VStack>
                    </CardBody>
                  </Card>
                </VStack>
              </TabPanel>

              {/* Attendance Tab */}
              <TabPanel>
                <VStack spacing={6} align="stretch">
                  <Card>
                    <CardHeader>
                      <Heading size="sm">Attendance Management</Heading>
                    </CardHeader>
                    <CardBody>
                      <VStack align="stretch" spacing={4}>
                        <HStack justify="space-between">
                          <Text>Quick attendance recording for classes</Text>
                          <Button colorScheme="blue" onClick={onOpen}>Record Attendance</Button>
                        </HStack>
                        
                        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
                          {classes.map((cls) => (
                            <Card key={cls.id} variant="outline">
                              <CardBody>
                                <VStack align="stretch" spacing={3}>
                                  <Text fontWeight="bold">{cls.name}</Text>
                                  <Text fontSize="sm" color="gray.600">
                                    {students.filter(s => s.current_class === cls.name).length} students
                                  </Text>
                                  <Button 
                                    size="sm" 
                                    colorScheme="green" 
                                    onClick={() => openBulkAttendance(cls.id)}
                                  >
                                    Take Attendance
                                  </Button>
                                </VStack>
                              </CardBody>
                            </Card>
                          ))}
                        </SimpleGrid>

                        {attendance.length > 0 && (
                          <Box>
                            <Heading size="sm" mb={3}>Recent Attendance Records</Heading>
                            <Box borderWidth="1px" rounded="md" p={3} maxH="300px" overflowY="auto">
                              <Table size="sm" variant="simple">
                                <Thead>
                                  <Tr>
                                    <Th>Date</Th>
                                    <Th>Student</Th>
                                    <Th>Class</Th>
                                    <Th>Status</Th>
                                    <Th>Notes</Th>
                                  </Tr>
                                </Thead>
                                <Tbody>
                                  {attendance.slice(0, 20).map((a, idx) => (
                                    <Tr key={idx}>
                                      <Td>{new Date(a.date).toLocaleDateString()}</Td>
                                      <Td>{a.student_name}</Td>
                                      <Td>{a.class_name}</Td>
                                      <Td>
                                        <Badge colorScheme={
                                          a.status === 'present' ? 'green' : 
                                          a.status === 'late' ? 'yellow' : 
                                          a.status === 'excused' ? 'blue' : 'red'
                                        }>
                                          {a.status}
                                        </Badge>
                                      </Td>
                                      <Td>{a.notes || '-'}</Td>
                                    </Tr>
                                  ))}
                                </Tbody>
                              </Table>
                            </Box>
                          </Box>
                        )}
                      </VStack>
                    </CardBody>
                  </Card>
                </VStack>
              </TabPanel>

              {/* Exam Schedule Tab */}
              <TabPanel>
                <VStack spacing={6} align="stretch">
                  <Card>
                    <CardHeader>
                      <Heading size="sm">Schedule Examinations</Heading>
                    </CardHeader>
                    <CardBody>
                      <VStack align="stretch" spacing={3}>
                        <HStack>
                          <FormControl isRequired>
                            <FormLabel>Exam Title</FormLabel>
                            <Input value={examForm.title} onChange={(e) => setExamForm({ ...examForm, title: e.target.value })} placeholder="e.g. Mid-Term Mathematics" />
                          </FormControl>
                          <FormControl isRequired>
                            <FormLabel>Subject</FormLabel>
                            <Select placeholder="Select" value={examForm.subject_id} onChange={(e) => setExamForm({ ...examForm, subject_id: e.target.value })}>
                              {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                            </Select>
                          </FormControl>
                          <FormControl isRequired>
                            <FormLabel>Class</FormLabel>
                            <Select placeholder="Select" value={examForm.class_id} onChange={(e) => setExamForm({ ...examForm, class_id: e.target.value })}>
                              {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                            </Select>
                          </FormControl>
                        </HStack>
                        <HStack>
                          <FormControl isRequired>
                            <FormLabel>Exam Date</FormLabel>
                            <Input type="date" value={examForm.exam_date} onChange={(e) => setExamForm({ ...examForm, exam_date: e.target.value })} />
                          </FormControl>
                          <FormControl>
                            <FormLabel>Start Time</FormLabel>
                            <Input type="time" value={examForm.start_time} onChange={(e) => setExamForm({ ...examForm, start_time: e.target.value })} />
                          </FormControl>
                          <FormControl>
                            <FormLabel>Duration (minutes)</FormLabel>
                            <NumberInput value={examForm.duration} onChange={(_, value) => setExamForm({ ...examForm, duration: value })} min={30} max={300}>
                              <NumberInputField />
                            </NumberInput>
                          </FormControl>
                          <FormControl>
                            <FormLabel>Total Marks</FormLabel>
                            <NumberInput value={examForm.total_marks} onChange={(_, value) => setExamForm({ ...examForm, total_marks: value })} min={10} max={200}>
                              <NumberInputField />
                            </NumberInput>
                          </FormControl>
                        </HStack>
                        <Button colorScheme="blue" onClick={createExam}>Schedule Exam</Button>
                      </VStack>
                    </CardBody>
                  </Card>

                  {examSchedules.length > 0 && (
                    <Card>
                      <CardHeader>
                        <Heading size="sm">Upcoming Examinations</Heading>
                      </CardHeader>
                      <CardBody>
                        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
                          {examSchedules.map((exam, idx) => (
                            <Card key={idx} variant="outline">
                              <CardBody>
                                <VStack align="start" spacing={2}>
                                  <Text fontWeight="bold">{exam.title}</Text>
                                  <Text fontSize="sm" color="gray.600">{exam.subject_name}</Text>
                                  <Text fontSize="sm" color="gray.600">{exam.class_name}</Text>
                                  <Text fontSize="sm" color="gray.600">
                                    {new Date(exam.exam_date).toLocaleDateString()}
                                  </Text>
                                  <Text fontSize="sm" color="gray.600">
                                    {exam.start_time} ({exam.duration} min)
                                  </Text>
                                  <Text fontSize="sm" color="gray.600">
                                    Total: {exam.total_marks} marks
                                  </Text>
                                </VStack>
                              </CardBody>
                            </Card>
                          ))}
                        </SimpleGrid>
                      </CardBody>
                    </Card>
                  )}
                </VStack>
              </TabPanel>

              {/* Reports Tab */}
              <TabPanel>
                <VStack spacing={6} align="stretch">
                  <Card>
                    <CardHeader>
                      <Heading size="sm">Student Report Card</Heading>
                    </CardHeader>
                    <CardBody>
                      <HStack spacing={4} mb={4}>
                        <FormControl isRequired>
                          <FormLabel>Student</FormLabel>
                          <Select placeholder="Select" value={reportForm.student_id} onChange={(e) => setReportForm({ ...reportForm, student_id: e.target.value })}>
                            {students.map(st => (
                              <option key={st.id} value={st.id}>{st.first_name} {st.last_name} {st.admission_no ? `(${st.admission_no})` : ''}</option>
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
                        <Button colorScheme="blue" onClick={generateReport}>Generate Report</Button>
                      </HStack>
                      
                      {report && (
                        <Box borderWidth="1px" rounded="md" p={4} bg="gray.50">
                          <HStack justify="space-between" mb={4}>
                            <VStack align="start" spacing={1}>
                              <Heading size="md">{report.student.name} - {report.student.class}</Heading>
                              <Text color="gray.600">{report.term} {report.academic_year}</Text>
                            </VStack>
                            <Button leftIcon={<DownloadIcon />} onClick={exportPDF}>Export PDF</Button>
                          </HStack>
                          
                          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4} mb={4}>
                            {report.subjects.map((r: any, idx: number) => (
                              <Card key={idx} variant="outline">
                                <CardBody>
                                  <VStack align="start" spacing={2}>
                                    <Text fontWeight="bold">{r.subject_name} ({r.subject_code})</Text>
                                    <HStack justify="space-between" w="100%">
                                      <Text>CA:</Text>
                                      <Text fontWeight="medium">{r.ca_score ?? '-'}</Text>
                                    </HStack>
                                    <HStack justify="space-between" w="100%">
                                      <Text>Exam:</Text>
                                      <Text fontWeight="medium">{r.exam_score ?? '-'}</Text>
                                    </HStack>
                                    <HStack justify="space-between" w="100%">
                                      <Text>Overall:</Text>
                                      <Text fontWeight="medium">{r.overall_score ?? '-'}</Text>
                                    </HStack>
                                    <HStack justify="space-between" w="100%">
                                      <Text>Grade:</Text>
                                      <Badge colorScheme={r.grade === 'A' ? 'green' : r.grade === 'B' ? 'blue' : r.grade === 'C' ? 'yellow' : 'red'}>
                                        {r.grade ?? '-'}
                                      </Badge>
                                    </HStack>
                                  </VStack>
                                </CardBody>
                              </Card>
                            ))}
                          </SimpleGrid>
                          
                          <Box textAlign="center" p={4} bg="white" rounded="md">
                            <Text fontSize="lg" fontWeight="bold">
                              Overall Average: {report.overall_average ?? 'N/A'}
                            </Text>
                          </Box>
                        </Box>
                      )}
                    </CardBody>
                  </Card>
                </VStack>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </VStack>
      </Container>

      {/* Bulk Attendance Modal */}
      <Modal isOpen={isAttendanceOpen} onClose={onAttendanceClose} size="4xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Record Bulk Attendance - {classes.find(c => c.id === Number(attendanceForm.class_id))?.name}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack align="stretch" spacing={4}>
              <HStack>
                <FormControl>
                  <FormLabel>Date</FormLabel>
                  <Input type="date" value={attendanceForm.date} onChange={(e) => setAttendanceForm({...attendanceForm, date: e.target.value})} />
                </FormControl>
              </HStack>
              
              <Box maxH="400px" overflowY="auto">
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Student</Th>
                      <Th>Status</Th>
                      <Th>Notes</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {attendanceForm.bulk_records.map((record, idx) => {
                      const student = students.find(s => s.id === record.student_id)
                      return (
                        <Tr key={idx}>
                          <Td>{student ? `${student.first_name} ${student.last_name}` : 'Unknown'}</Td>
                          <Td>
                            <Select 
                              value={record.status} 
                              onChange={(e) => {
                                const newRecords = [...attendanceForm.bulk_records]
                                newRecords[idx].status = e.target.value
                                setAttendanceForm({...attendanceForm, bulk_records: newRecords})
                              }}
                            >
                              <option value="present">Present</option>
                              <option value="absent">Absent</option>
                              <option value="late">Late</option>
                              <option value="excused">Excused</option>
                            </Select>
                          </Td>
                          <Td>
                            <Input 
                              placeholder="Optional notes" 
                              value={record.notes}
                              onChange={(e) => {
                                const newRecords = [...attendanceForm.bulk_records]
                                newRecords[idx].notes = e.target.value
                                setAttendanceForm({...attendanceForm, bulk_records: newRecords})
                              }}
                            />
                          </Td>
                        </Tr>
                      )
                    })}
                  </Tbody>
                </Table>
              </Box>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onAttendanceClose}>Cancel</Button>
            <Button colorScheme="blue" onClick={saveBulkAttendance}>Save Attendance</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}


