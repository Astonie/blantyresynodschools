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
  Button,
  Select,
  FormControl,
  FormLabel,
  Badge,
  Alert,
  AlertIcon,
  useToast,
  Spinner,
  Center,
  IconButton,
  Tooltip,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Progress,
  Input,
  Textarea,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Checkbox,
  CheckboxGroup,
  Stack,
  Divider,
  Icon
} from '@chakra-ui/react'
import {
  FaCheck,
  FaTimes,
  FaExclamationTriangle,
  FaSave,
  FaCalendarCheck,
  FaUserCheck,
  FaUserTimes,
  FaFileExport,
  FaFilter,
  FaClock,
  FaComment,
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

interface AttendanceRecord {
  id?: number
  student_id: number
  class_id: number
  date: string
  status: 'present' | 'absent' | 'late' | 'excused'
  notes?: string
  student_name: string
  student_id_number: string
}

interface AttendanceStats {
  total_students: number
  present_today: number
  absent_today: number
  late_today: number
  overall_rate: number
  weekly_rate: number
  monthly_rate: number
}

const TeacherAttendanceManagement: React.FC = () => {
  const { className } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { isOpen, onOpen, onClose } = useDisclosure()
  
  const [students, setStudents] = useState<Student[]>([])
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>([])
  const [attendanceStats, setAttendanceStats] = useState<AttendanceStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
  const [bulkMode, setBulkMode] = useState(false)
  const [selectedStudents, setSelectedStudents] = useState<number[]>([])
  const [teacherAssignments, setTeacherAssignments] = useState<any[]>([])
  
  // Form state
  const [attendanceForm, setAttendanceForm] = useState({
    status: 'present' as 'present' | 'absent' | 'late' | 'excused',
    notes: ''
  })

  useEffect(() => {
    if (className) {
      fetchAttendanceData()
    } else {
      // If no className parameter, fetch teacher assignments to show selector
      fetchTeacherAssignments()
    }
  }, [className, selectedDate])

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

  const fetchAttendanceData = async () => {
    try {
      setLoading(true)
      
      // Fetch students in the class
      const studentsResponse = await api.get(`/teachers/classes/${className}/students`)
      setStudents(studentsResponse.data)
      
      // Fetch attendance records for selected date
      const attendanceResponse = await api.get(
        `/teachers/attendance/${className}/${selectedDate}`
      )
      setAttendanceRecords(attendanceResponse.data.records || [])
      
      // Fetch attendance statistics - commented out for now as endpoint doesn't exist
      // try {
      //   const statsResponse = await api.get(
      //     `/teachers/attendance/${className}/stats?date=${selectedDate}`
      //   )
      //   setAttendanceStats(statsResponse.data)
      // } catch (statsError) {
      //   // Stats endpoint might not exist, ignore error
      //   setAttendanceStats(null)
      // }
      setAttendanceStats(null) // Disable stats for now
      
    } catch (error: any) {
      console.error('Error fetching attendance data:', error)
      let errorMessage = 'Failed to load attendance data'
      
      if (error?.response?.status === 403) {
        errorMessage = 'You do not have permission to access this class attendance data'
      } else if (error?.response?.status === 404) {
        errorMessage = 'Class not found or no attendance data for this date'
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

  const getStudentAttendance = (studentId: number): AttendanceRecord | undefined => {
    return attendanceRecords.find(record => record.student_id === studentId)
  }

  const handleMarkAttendance = async (student: Student, status: 'present' | 'absent' | 'late' | 'excused', notes?: string) => {
    try {
      const existingRecord = getStudentAttendance(student.id)
      
      const payload = {
        student_id: student.id,
        class_name: className,
        date: selectedDate,
        status: status,
        notes: notes || null
      }
      
      if (existingRecord?.id) {
        // Update existing record
        await api.put(`/teachers/attendance/${existingRecord.id}`, payload)
      } else {
        // Create new record
        await api.post('/teachers/attendance', payload)
      }
      
      // Refresh data
      await fetchAttendanceData()
      
      toast({
        title: 'Success',
        description: `Marked ${student.full_name} as ${status}`,
        status: 'success',
        duration: 2000,
        isClosable: true
      })
      
    } catch (error) {
      console.error('Error marking attendance:', error)
      toast({
        title: 'Error',
        description: 'Failed to mark attendance',
        status: 'error',
        duration: 3000,
        isClosable: true
      })
    }
  }

  const handleBulkAttendance = async () => {
    try {
      setSaving(true)
      
      const promises = selectedStudents.map(studentId => {
        const student = students.find(s => s.id === studentId)
        if (student) {
          return handleMarkAttendance(student, attendanceForm.status, attendanceForm.notes)
        }
        return Promise.resolve()
      })
      
      await Promise.all(promises)
      
      setSelectedStudents([])
      setBulkMode(false)
      onClose()
      
      toast({
        title: 'Success',
        description: `Marked attendance for ${selectedStudents.length} students`,
        status: 'success',
        duration: 3000,
        isClosable: true
      })
      
    } catch (error) {
      console.error('Error with bulk attendance:', error)
      toast({
        title: 'Error',
        description: 'Failed to mark bulk attendance',
        status: 'error',
        duration: 3000,
        isClosable: true
      })
    } finally {
      setSaving(false)
    }
  }

  const handleEditAttendance = (student: Student) => {
    const record = getStudentAttendance(student.id)
    setSelectedStudent(student)
    setAttendanceForm({
      status: record?.status || 'present',
      notes: record?.notes || ''
    })
    onOpen()
  }

  const handleSaveAttendance = async () => {
    if (!selectedStudent) return
    
    try {
      setSaving(true)
      await handleMarkAttendance(selectedStudent, attendanceForm.status, attendanceForm.notes)
      onClose()
    } catch (error) {
      // Error is already handled in handleMarkAttendance
    } finally {
      setSaving(false)
    }
  }

  const markAllPresent = async () => {
    try {
      setSaving(true)
      
      const unmarkedStudents = students.filter(student => !getStudentAttendance(student.id))
      
      const promises = unmarkedStudents.map(student => 
        handleMarkAttendance(student, 'present')
      )
      
      await Promise.all(promises)
      
      toast({
        title: 'Success',
        description: `Marked ${unmarkedStudents.length} students as present`,
        status: 'success',
        duration: 3000,
        isClosable: true
      })
      
    } catch (error) {
      // Error handling is done in individual calls
    } finally {
      setSaving(false)
    }
  }

  const exportAttendance = async () => {
    try {
      const response = await api.get(
        `/teachers/attendance/${className}/export?date=${selectedDate}`,
        { responseType: 'blob' }
      )
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${className}_attendance_${selectedDate}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to export attendance',
        status: 'error',
        duration: 3000,
        isClosable: true
      })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'present': return 'green'
      case 'absent': return 'red'
      case 'late': return 'yellow'
      case 'excused': return 'blue'
      default: return 'gray'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'present': return FaCheck
      case 'absent': return FaTimes
      case 'late': return FaClock
      case 'excused': return FaUserCheck
      default: return FaExclamationTriangle
    }
  }

  if (loading) {
    return (
      <Center h="400px">
        <VStack>
          <Spinner size="lg" color="blue.500" />
          <Text>Loading attendance data...</Text>
        </VStack>
      </Center>
    )
  }

  // If no className parameter, show class selector
  if (!className) {
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
            Attendance Management
          </Heading>
          
          <Alert status="info">
            <AlertIcon />
            Please select a class to manage attendance.
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
                          onClick={() => navigate(`/teacher/attendance/${assignment.class_name}`)}>
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
          Attendance Management: {className}
        </Heading>
        
        <HStack spacing={4} wrap="wrap">
          <FormControl maxW="200px">
            <FormLabel fontSize="sm">Date</FormLabel>
            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              size="sm"
            />
          </FormControl>
          
          <Button 
            leftIcon={<FaUserCheck />} 
            colorScheme="green" 
            variant="outline" 
            size="sm"
            onClick={markAllPresent}
            isLoading={saving}
          >
            Mark All Present
          </Button>
          
          <Button 
            leftIcon={<FaFilter />} 
            colorScheme="blue" 
            variant="outline" 
            size="sm"
            onClick={() => {
              setBulkMode(!bulkMode)
              setSelectedStudents([])
            }}
          >
            {bulkMode ? 'Exit Bulk Mode' : 'Bulk Mode'}
          </Button>
          
          <Button 
            leftIcon={<FaFileExport />} 
            colorScheme="purple" 
            variant="outline" 
            size="sm"
            onClick={exportAttendance}
          >
            Export
          </Button>
        </HStack>
      </VStack>

      {/* Statistics */}
      {attendanceStats && (
        <Card mb={6}>
          <CardHeader>
            <Heading size="md">Attendance Statistics - {new Date(selectedDate).toLocaleDateString()}</Heading>
          </CardHeader>
          <CardBody>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
              <Stat>
                <StatLabel>Present Today</StatLabel>
                <StatNumber color="green.500">{attendanceStats.present_today}</StatNumber>
                <StatHelpText>out of {attendanceStats.total_students} students</StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>Absent Today</StatLabel>
                <StatNumber color="red.500">{attendanceStats.absent_today}</StatNumber>
                <Progress 
                  value={(attendanceStats.absent_today / attendanceStats.total_students) * 100} 
                  colorScheme="red" 
                  size="sm" 
                  mt={2} 
                />
              </Stat>
              <Stat>
                <StatLabel>Late Today</StatLabel>
                <StatNumber color="yellow.500">{attendanceStats.late_today}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>Overall Rate</StatLabel>
                <StatNumber>{attendanceStats.overall_rate.toFixed(1)}%</StatNumber>
                <StatHelpText>This month: {attendanceStats.monthly_rate.toFixed(1)}%</StatHelpText>
              </Stat>
            </SimpleGrid>
          </CardBody>
        </Card>
      )}

      {/* Bulk Mode Alert */}
      {bulkMode && (
        <Alert status="info" mb={4}>
          <AlertIcon />
          <VStack align="start" flex={1}>
            <Text fontWeight="bold">Bulk Mode Active</Text>
            <HStack>
              <Text>Select students and choose an action:</Text>
              <Button
                size="sm"
                colorScheme="blue"
                onClick={onOpen}
                isDisabled={selectedStudents.length === 0}
              >
                Mark Selected ({selectedStudents.length})
              </Button>
            </HStack>
          </VStack>
        </Alert>
      )}

      {/* Student Attendance Table */}
      <Card>
        <CardHeader>
          <HStack justify="space-between">
            <Heading size="md">Student Attendance</Heading>
            <Text fontSize="sm" color="gray.600">
              {attendanceRecords.length} of {students.length} students marked
            </Text>
          </HStack>
        </CardHeader>
        <CardBody>
          <Box overflowX="auto">
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  {bulkMode && <Th>Select</Th>}
                  <Th>Student ID</Th>
                  <Th>Student Name</Th>
                  <Th>Status</Th>
                  <Th>Time Marked</Th>
                  <Th>Notes</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {students.map((student) => {
                  const record = getStudentAttendance(student.id)
                  const isMarked = !!record && !!record.status
                  
                  return (
                    <Tr key={student.id}>
                      {bulkMode && (
                        <Td>
                          <Checkbox
                            isChecked={selectedStudents.includes(student.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedStudents(prev => [...prev, student.id])
                              } else {
                                setSelectedStudents(prev => prev.filter(id => id !== student.id))
                              }
                            }}
                          />
                        </Td>
                      )}
                      <Td fontWeight="medium">{student.student_id}</Td>
                      <Td>{student.full_name}</Td>
                      <Td>
                        {isMarked ? (
                          <Badge 
                            colorScheme={getStatusColor(record.status)}
                            variant="solid"
                            display="flex"
                            alignItems="center"
                            w="fit-content"
                          >
                            <Box as={getStatusIcon(record.status)} mr={1} />
                            {record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                          </Badge>
                        ) : (
                          <Badge colorScheme="gray" variant="outline">
                            Not Marked
                          </Badge>
                        )}
                      </Td>
                      <Td>
                        {record?.id ? (
                          <Text fontSize="sm">
                            {new Date().toLocaleTimeString('en-US', { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </Text>
                        ) : (
                          <Text color="gray.400" fontSize="sm">-</Text>
                        )}
                      </Td>
                      <Td>
                        {record?.notes ? (
                          <Tooltip label={record.notes}>
                            <Badge colorScheme="blue" variant="subtle" cursor="pointer">
                              <FaComment /> Note
                            </Badge>
                          </Tooltip>
                        ) : (
                          <Text color="gray.400" fontSize="sm">-</Text>
                        )}
                      </Td>
                      <Td>
                        <HStack spacing={2}>
                          {!bulkMode && (
                            <>
                              <Tooltip label="Mark Present">
                                <IconButton
                                  aria-label="Mark present"
                                  icon={<FaCheck />}
                                  size="sm"
                                  colorScheme="green"
                                  variant={record?.status === 'present' ? 'solid' : 'ghost'}
                                  onClick={() => handleMarkAttendance(student, 'present')}
                                />
                              </Tooltip>
                              <Tooltip label="Mark Absent">
                                <IconButton
                                  aria-label="Mark absent"
                                  icon={<FaTimes />}
                                  size="sm"
                                  colorScheme="red"
                                  variant={record?.status === 'absent' ? 'solid' : 'ghost'}
                                  onClick={() => handleMarkAttendance(student, 'absent')}
                                />
                              </Tooltip>
                              <Tooltip label="Mark Late">
                                <IconButton
                                  aria-label="Mark late"
                                  icon={<FaClock />}
                                  size="sm"
                                  colorScheme="yellow"
                                  variant={record?.status === 'late' ? 'solid' : 'ghost'}
                                  onClick={() => handleMarkAttendance(student, 'late')}
                                />
                              </Tooltip>
                            </>
                          )}
                          <Tooltip label="Edit Details">
                            <IconButton
                              aria-label="Edit attendance"
                              icon={<FaComment />}
                              size="sm"
                              colorScheme="blue"
                              variant="ghost"
                              onClick={() => handleEditAttendance(student)}
                            />
                          </Tooltip>
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

      {/* Edit Attendance Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {bulkMode 
              ? `Mark Attendance for ${selectedStudents.length} Students`
              : `Edit Attendance: ${selectedStudent?.full_name}`
            }
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Status</FormLabel>
                <Select
                  value={attendanceForm.status}
                  onChange={(e) => setAttendanceForm(prev => ({
                    ...prev, 
                    status: e.target.value as 'present' | 'absent' | 'late' | 'excused'
                  }))}
                >
                  <option value="present">Present</option>
                  <option value="absent">Absent</option>
                  <option value="late">Late</option>
                  <option value="excused">Excused</option>
                </Select>
              </FormControl>
              
              <FormControl>
                <FormLabel>Notes (Optional)</FormLabel>
                <Textarea
                  value={attendanceForm.notes}
                  onChange={(e) => setAttendanceForm(prev => ({...prev, notes: e.target.value}))}
                  placeholder="Add any relevant notes..."
                  rows={3}
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
              onClick={bulkMode ? handleBulkAttendance : handleSaveAttendance}
              isLoading={saving}
              loadingText="Saving..."
            >
              Save
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default TeacherAttendanceManagement
