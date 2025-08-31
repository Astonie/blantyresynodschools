import React, { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Text,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Input,
  Button,
  Select,
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  Badge,
  Alert,
  AlertIcon,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Spinner,
  Center,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  IconButton,
  Tooltip,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
  Icon
} from '@chakra-ui/react'
import {
  FaSave,
  FaEdit,
  FaEye,
  FaDownload,
  FaPlus,
  FaFilter,
  FaChartBar,
  FaFileExport,
  FaChalkboardTeacher,
  FaBookOpen,
  FaUsers
} from 'react-icons/fa'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

interface Student {
  id: number
  student_id: string
  full_name: string
  class_name: string
}

interface AcademicRecord {
  id?: number
  student_id: number
  subject_id: number
  ca_score?: number
  exam_score?: number
  overall_score?: number
  grade?: string
  grade_points?: number
  term: string
  academic_year: string
  comments?: string
  student_name: string
  student_id_number: string
}

interface ClassStats {
  total_students: number
  graded_students: number
  average_score: number
  highest_score: number
  lowest_score: number
  grade_distribution: { [key: string]: number }
}

const TeacherGradeManagement: React.FC = () => {
  const { className, subjectCode } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { isOpen, onOpen, onClose } = useDisclosure()
  
  const [students, setStudents] = useState<Student[]>([])
  const [academicRecords, setAcademicRecords] = useState<AcademicRecord[]>([])
  const [classStats, setClassStats] = useState<ClassStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [selectedTerm, setSelectedTerm] = useState('Term 1 Final')
  const [selectedYear, setSelectedYear] = useState('2024')
  const [editingRecord, setEditingRecord] = useState<AcademicRecord | null>(null)
  const [bulkUpdateMode, setBulkUpdateMode] = useState(false)
  const [teacherAssignments, setTeacherAssignments] = useState<any[]>([])

  // Form state for editing grades
  const [gradeForm, setGradeForm] = useState({
    ca_score: '',
    exam_score: '',
    overall_score: '',
    comments: ''
  })

  useEffect(() => {
    if (className && subjectCode) {
      fetchClassData()
    } else {
      // If no parameters, fetch teacher assignments to show selector
      fetchTeacherAssignments()
    }
  }, [className, subjectCode, selectedTerm, selectedYear])

  const fetchTeacherAssignments = async () => {
    try {
      setLoading(true)
      const response = await api.get('/teachers/dashboard')
      setTeacherAssignments(response.data.assignments || [])
    } catch (error: any) {
      console.error('Error fetching teacher assignments:', error)
      toast({
        title: 'Error',
        description: 'Failed to load your class assignments',
        status: 'error',
        duration: 5000,
        isClosable: true
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchClassData = async () => {
    try {
      setLoading(true)
      
      // Fetch students in the class
      const studentsResponse = await api.get(`/teachers/classes/${className}/students`)
      setStudents(studentsResponse.data)
      
      // Fetch existing academic records
      const recordsResponse = await api.get(
        `/teachers/grades/${className}/${subjectCode}?term=${selectedTerm}&academic_year=${selectedYear}`
      )
      setAcademicRecords(recordsResponse.data.records || [])
      
      // Fetch class statistics
      try {
        const statsResponse = await api.get(
          `/teachers/grades/${className}/${subjectCode}/stats?term=${selectedTerm}&academic_year=${selectedYear}`
        )
        setClassStats(statsResponse.data)
      } catch (statsError) {
        // Stats endpoint might not exist, ignore error
        setClassStats(null)
      }
      
    } catch (error: any) {
      console.error('Error fetching class data:', error)
      let errorMessage = 'Failed to load class data'
      
      if (error?.response?.status === 403) {
        errorMessage = 'You do not have permission to access this class data'
      } else if (error?.response?.status === 404) {
        errorMessage = 'Class or subject not found'
      } else if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail
      }
      
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true
      })
    } finally {
      setLoading(false)
    }
  }

  const getStudentRecord = (studentId: number): AcademicRecord | undefined => {
    return academicRecords.find(record => record.student_id === studentId)
  }

  const handleEditGrade = (student: Student) => {
    const record = getStudentRecord(student.id)
    setEditingRecord(record || {
      student_id: student.id,
      subject_id: 0, // Will be set by backend
      term: selectedTerm,
      academic_year: selectedYear,
      student_name: student.full_name,
      student_id_number: student.student_id
    })
    
    setGradeForm({
      ca_score: record?.ca_score?.toString() || '',
      exam_score: record?.exam_score?.toString() || '',
      overall_score: record?.overall_score?.toString() || '',
      comments: record?.comments || ''
    })
    
    onOpen()
  }

  const handleSaveGrade = async () => {
    if (!editingRecord) return
    
    try {
      setSaving(true)
      
      const payload = {
        student_id: editingRecord.student_id,
        class_name: className,
        subject_code: subjectCode,
        ca_score: gradeForm.ca_score ? parseFloat(gradeForm.ca_score) : null,
        exam_score: gradeForm.exam_score ? parseFloat(gradeForm.exam_score) : null,
        overall_score: gradeForm.overall_score ? parseFloat(gradeForm.overall_score) : null,
        term: selectedTerm,
        academic_year: selectedYear,
        comments: gradeForm.comments || null
      }
      
      console.log('Sending grade payload:', payload) // Debug log
      
      // Always use POST as backend handles both create and update
      await api.post('/teachers/grades', payload)
      
      toast({
        title: 'Success',
        description: 'Grade saved successfully',
        status: 'success',
        duration: 3000,
        isClosable: true
      })
      
      onClose()
      fetchClassData() // Refresh data
      
    } catch (error) {
      console.error('Error saving grade:', error)
      toast({
        title: 'Error',
        description: 'Failed to save grade',
        status: 'error',
        duration: 3000,
        isClosable: true
      })
    } finally {
      setSaving(false)
    }
  }

  const handleBulkExport = async () => {
    try {
      const response = await api.get(
        `/teachers/grades/${className}/${subjectCode}/export?term=${selectedTerm}&academic_year=${selectedYear}`,
        { responseType: 'blob' }
      )
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${className}_${subjectCode}_${selectedTerm}_${selectedYear}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to export grades',
        status: 'error',
        duration: 3000,
        isClosable: true
      })
    }
  }

  const getGradeColor = (grade?: string) => {
    if (!grade) return 'gray'
    if (grade === 'A') return 'green'
    if (grade === 'B') return 'blue'
    if (grade === 'C') return 'yellow'
    if (grade === 'D') return 'orange'
    return 'red'
  }

  if (loading) {
    return (
      <Center h="400px">
        <VStack>
          <Spinner size="lg" color="blue.500" />
          <Text>Loading grade management...</Text>
        </VStack>
      </Center>
    )
  }

  // If no class/subject parameters, show selector
  if (!className || !subjectCode) {
    return (
      <Box p={6} maxW="4xl" mx="auto">
        <VStack align="start" spacing={6}>
          <Button 
            variant="ghost" 
            onClick={() => navigate('/teacher/dashboard')}
            size="sm"
          >
            ← Back to Dashboard
          </Button>
          
          <Heading size="lg" color="blue.600">
            Grade Management
          </Heading>
          
          <Alert status="info">
            <AlertIcon />
            Please select a class and subject to manage grades.
          </Alert>
          
          {teacherAssignments.length > 0 ? (
            <Card w="full">
              <CardHeader>
                <Heading size="md">Your Class Assignments</Heading>
              </CardHeader>
              <CardBody>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  {teacherAssignments.map((assignment) => (
                    <Card key={assignment.id} variant="outline" cursor="pointer" _hover={{ shadow: 'md' }}
                          onClick={() => navigate(`/teacher/grades/${assignment.class_name}/${assignment.subject_code}`)}>
                      <CardBody>
                        <VStack align="start" spacing={2}>
                          <HStack>
                            <Icon as={FaChalkboardTeacher} color="blue.500" />
                            <Text fontWeight="bold" color="blue.600">{assignment.class_name}</Text>
                          </HStack>
                          <HStack>
                            <Icon as={FaBookOpen} color="green.500" />
                            <Text>{assignment.subject_name} ({assignment.subject_code})</Text>
                          </HStack>
                          <HStack>
                            <Icon as={FaUsers} color="orange.500" />
                            <Text fontSize="sm" color="gray.600">{assignment.student_count} students</Text>
                          </HStack>
                        </VStack>
                      </CardBody>
                    </Card>
                  ))}
                </SimpleGrid>
              </CardBody>
            </Card>
          ) : (
            <Alert status="warning">
              <AlertIcon />
              No class assignments found. Please contact your administrator.
            </Alert>
          )}
        </VStack>
      </Box>
    )
  }

  return (
    <Box p={6} maxW="7xl" mx="auto">
      {/* Header */}
      <VStack align="start" spacing={4} mb={6}>
        <Button 
          variant="ghost" 
          onClick={() => navigate('/teacher/dashboard')}
          size="sm"
        >
          ← Back to Dashboard
        </Button>
        
        <Heading size="lg" color="blue.600">
          Grade Management: {className} - {subjectCode}
        </Heading>
        
        <HStack spacing={4} wrap="wrap">
          <FormControl maxW="200px">
            <FormLabel fontSize="sm">Academic Year</FormLabel>
            <Select 
              value={selectedYear} 
              onChange={(e) => setSelectedYear(e.target.value)}
              size="sm"
            >
              <option value="2024">2024</option>
              <option value="2023">2023</option>
            </Select>
          </FormControl>
          
          <FormControl maxW="200px">
            <FormLabel fontSize="sm">Term</FormLabel>
            <Select 
              value={selectedTerm} 
              onChange={(e) => setSelectedTerm(e.target.value)}
              size="sm"
            >
              <option value="Term 1 Mid">Term 1 Mid</option>
              <option value="Term 1 Final">Term 1 Final</option>
              <option value="Term 2 Mid">Term 2 Mid</option>
              <option value="Term 2 Final">Term 2 Final</option>
              <option value="Term 3 Mid">Term 3 Mid</option>
              <option value="Term 3 Final">Term 3 Final</option>
            </Select>
          </FormControl>
          
          <Button 
            leftIcon={<FaFileExport />} 
            colorScheme="green" 
            variant="outline" 
            size="sm"
            onClick={handleBulkExport}
          >
            Export Grades
          </Button>
        </HStack>
      </VStack>

      {/* Statistics */}
      {classStats && (
        <Card mb={6}>
          <CardHeader>
            <Heading size="md">Class Statistics</Heading>
          </CardHeader>
          <CardBody>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 5 }} spacing={6}>
              <Stat>
                <StatLabel>Total Students</StatLabel>
                <StatNumber>{classStats.total_students}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>Graded Students</StatLabel>
                <StatNumber>{classStats.graded_students}</StatNumber>
                <Progress 
                  value={(classStats.graded_students / classStats.total_students) * 100} 
                  colorScheme="blue" 
                  size="sm" 
                  mt={2} 
                />
              </Stat>
              <Stat>
                <StatLabel>Class Average</StatLabel>
                <StatNumber>{classStats.average_score.toFixed(1)}%</StatNumber>
                <StatHelpText>Overall average score</StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>Highest Score</StatLabel>
                <StatNumber color="green.500">{classStats.highest_score}%</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>Lowest Score</StatLabel>
                <StatNumber color="orange.500">{classStats.lowest_score}%</StatNumber>
              </Stat>
            </SimpleGrid>
          </CardBody>
        </Card>
      )}

      {/* Student Grades Table */}
      <Card>
        <CardHeader>
          <HStack justify="space-between">
            <Heading size="md">Student Grades</Heading>
            <HStack>
              <Text fontSize="sm" color="gray.600">
                {academicRecords.length} of {students.length} students graded
              </Text>
            </HStack>
          </HStack>
        </CardHeader>
        <CardBody>
          <Box overflowX="auto">
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>Student ID</Th>
                  <Th>Student Name</Th>
                  <Th>CA Score</Th>
                  <Th>Exam Score</Th>
                  <Th>Overall</Th>
                  <Th>Grade</Th>
                  <Th>Points</Th>
                  <Th>Status</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {students.map((student) => {
                  const record = getStudentRecord(student.id)
                  const hasGrades = record && (record.ca_score || record.exam_score || record.overall_score)
                  
                  return (
                    <Tr key={student.id}>
                      <Td fontWeight="medium">{student.student_id}</Td>
                      <Td>{student.full_name}</Td>
                      <Td>
                        {record?.ca_score ? (
                          <Text>{record.ca_score}%</Text>
                        ) : (
                          <Text color="gray.400">-</Text>
                        )}
                      </Td>
                      <Td>
                        {record?.exam_score ? (
                          <Text>{record.exam_score}%</Text>
                        ) : (
                          <Text color="gray.400">-</Text>
                        )}
                      </Td>
                      <Td>
                        {record?.overall_score ? (
                          <Text fontWeight="bold">{record.overall_score}%</Text>
                        ) : (
                          <Text color="gray.400">-</Text>
                        )}
                      </Td>
                      <Td>
                        {record?.grade ? (
                          <Badge colorScheme={getGradeColor(record.grade)}>
                            {record.grade}
                          </Badge>
                        ) : (
                          <Text color="gray.400">-</Text>
                        )}
                      </Td>
                      <Td>
                        {record?.grade_points && typeof record.grade_points === 'number' ? (
                          <Text>{record.grade_points.toFixed(1)}</Text>
                        ) : (
                          <Text color="gray.400">-</Text>
                        )}
                      </Td>
                      <Td>
                        <Badge 
                          colorScheme={hasGrades ? "green" : "orange"}
                          variant="subtle"
                        >
                          {hasGrades ? "Graded" : "Pending"}
                        </Badge>
                      </Td>
                      <Td>
                        <HStack spacing={2}>
                          <Tooltip label="Edit Grade">
                            <IconButton
                              aria-label="Edit grade"
                              icon={<FaEdit />}
                              size="sm"
                              colorScheme="blue"
                              variant="ghost"
                              onClick={() => handleEditGrade(student)}
                            />
                          </Tooltip>
                          {hasGrades && (
                            <Tooltip label="View Details">
                              <IconButton
                                aria-label="View details"
                                icon={<FaEye />}
                                size="sm"
                                colorScheme="gray"
                                variant="ghost"
                                onClick={() => {
                                  // Add view details functionality
                                }}
                              />
                            </Tooltip>
                          )}
                        </HStack>
                      </Td>
                    </Tr>
                  )
                })}
              </Tbody>
            </Table>
          </Box>
        </CardBody>
      </Card>

      {/* Grade Edit Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            Edit Grade: {editingRecord?.student_name}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Alert status="info" size="sm">
                <AlertIcon />
                Enter scores out of 100. Overall score will be calculated automatically if left blank.
              </Alert>
              
              <SimpleGrid columns={2} spacing={4}>
                <FormControl>
                  <FormLabel>Continuous Assessment (%)</FormLabel>
                  <NumberInput
                    value={gradeForm.ca_score}
                    onChange={(value) => setGradeForm(prev => ({...prev, ca_score: value}))}
                    min={0}
                    max={100}
                    precision={1}
                  >
                    <NumberInputField placeholder="e.g., 85.5" />
                  </NumberInput>
                </FormControl>
                
                <FormControl>
                  <FormLabel>Exam Score (%)</FormLabel>
                  <NumberInput
                    value={gradeForm.exam_score}
                    onChange={(value) => setGradeForm(prev => ({...prev, exam_score: value}))}
                    min={0}
                    max={100}
                    precision={1}
                  >
                    <NumberInputField placeholder="e.g., 78.0" />
                  </NumberInput>
                </FormControl>
              </SimpleGrid>
              
              <FormControl>
                <FormLabel>Overall Score (%) - Optional</FormLabel>
                <NumberInput
                  value={gradeForm.overall_score}
                  onChange={(value) => setGradeForm(prev => ({...prev, overall_score: value}))}
                  min={0}
                  max={100}
                  precision={1}
                >
                  <NumberInputField placeholder="Leave blank for auto-calculation" />
                </NumberInput>
                <Text fontSize="sm" color="gray.600" mt={1}>
                  If not provided, will be calculated as: CA (40%) + Exam (60%)
                </Text>
              </FormControl>
              
              <FormControl>
                <FormLabel>Teacher Comments</FormLabel>
                <Input
                  value={gradeForm.comments}
                  onChange={(e) => setGradeForm(prev => ({...prev, comments: e.target.value}))}
                  placeholder="Optional comments about student's performance"
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="blue" 
              onClick={handleSaveGrade}
              isLoading={saving}
              loadingText="Saving..."
            >
              Save Grade
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default TeacherGradeManagement
