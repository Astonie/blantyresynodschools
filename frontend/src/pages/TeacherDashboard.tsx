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
  Grid,
  GridItem,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Badge,
  Button,
  Icon,
  SimpleGrid,
  Avatar,
  Progress,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Alert,
  AlertIcon,
  useColorModeValue
} from '@chakra-ui/react'
import {
  FaChalkboardTeacher,
  FaUsers,
  FaBookOpen,
  FaClipboardList,
  FaCalendarCheck,
  FaTrophy,
  FaChartLine,
  FaClock,
  FaExclamationTriangle,
  FaBell,
  FaPlus
} from 'react-icons/fa'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

interface TeacherDashboardData {
  teacher_info: {
    id: number
    full_name: string
    email: string
    specialization?: string
    classes_assigned: number
    subjects_taught: number
  }
  assignments: Array<{
    id: number
    class_name: string
    subject_name: string
    subject_code: string
    student_count: number
    is_primary: boolean
  }>
  recent_activities: Array<{
    id: number
    type: string
    description: string
    date: string
  }>
  statistics: {
    total_students: number
    classes_today: number
    pending_grades: number
    attendance_rate: number
  }
  upcoming_classes: Array<{
    class_name: string
    subject_name: string
    time: string
    room?: string
  }>
  notifications: Array<{
    id: number
    title: string
    message: string
    type: 'info' | 'warning' | 'success'
    date: string
  }>
}

const TeacherDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<TeacherDashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  
  const cardBg = useColorModeValue('white', 'gray.800')
  const statBg = useColorModeValue('blue.50', 'blue.900')

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const response = await api.get('/teachers/dashboard')
      setDashboardData(response.data)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box p={6}>
        <Text>Loading dashboard...</Text>
      </Box>
    )
  }

  if (!dashboardData) {
    return (
      <Box p={6}>
        <Alert status="error">
          <AlertIcon />
          Failed to load dashboard data
        </Alert>
      </Box>
    )
  }

  const { teacher_info, assignments, statistics, recent_activities, upcoming_classes, notifications } = dashboardData

  return (
    <Box p={6} maxW="7xl" mx="auto">
      {/* Header Section */}
      <VStack align="start" spacing={4} mb={8}>
        <HStack spacing={4}>
          <Avatar size="lg" name={teacher_info.full_name} />
          <VStack align="start" spacing={1}>
            <Heading size="lg" color="blue.600">
              Welcome, {teacher_info.full_name}
            </Heading>
            <Text color="gray.600" fontSize="md">
              {teacher_info.specialization && `${teacher_info.specialization} Teacher`}
            </Text>
            <HStack spacing={4}>
              <Badge colorScheme="blue" variant="subtle">
                {teacher_info.classes_assigned} Classes
              </Badge>
              <Badge colorScheme="green" variant="subtle">
                {teacher_info.subjects_taught} Subjects
              </Badge>
            </HStack>
          </VStack>
        </HStack>
      </VStack>

      {/* Quick Stats */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Card bg={statBg}>
          <CardBody>
            <Stat>
              <HStack>
                <Box>
                  <StatLabel>Total Students</StatLabel>
                  <StatNumber>{statistics.total_students}</StatNumber>
                </Box>
                <Icon as={FaUsers} boxSize={8} color="blue.500" />
              </HStack>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={statBg}>
          <CardBody>
            <Stat>
              <HStack>
                <Box>
                  <StatLabel>Classes Today</StatLabel>
                  <StatNumber>{statistics.classes_today}</StatNumber>
                </Box>
                <Icon as={FaCalendarCheck} boxSize={8} color="green.500" />
              </HStack>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={statBg}>
          <CardBody>
            <Stat>
              <HStack>
                <Box>
                  <StatLabel>Pending Grades</StatLabel>
                  <StatNumber color={statistics.pending_grades > 0 ? "orange.500" : "green.500"}>
                    {statistics.pending_grades}
                  </StatNumber>
                </Box>
                <Icon as={FaClipboardList} boxSize={8} color="orange.500" />
              </HStack>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={statBg}>
          <CardBody>
            <Stat>
              <HStack>
                <Box>
                  <StatLabel>Attendance Rate</StatLabel>
                  <StatNumber>{statistics.attendance_rate}%</StatNumber>
                  <Progress value={statistics.attendance_rate} colorScheme="blue" size="sm" mt={2} />
                </Box>
                <Icon as={FaChartLine} boxSize={8} color="purple.500" />
              </HStack>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Main Content Tabs */}
      <Tabs variant="enclosed" colorScheme="blue">
        <TabList>
          <Tab>My Classes</Tab>
          <Tab>Grade Management</Tab>
          <Tab>Attendance</Tab>
          <Tab>Schedule</Tab>
          <Tab>Notifications</Tab>
        </TabList>

        <TabPanels>
          {/* My Classes Tab */}
          <TabPanel>
            <VStack align="stretch" spacing={6}>
              <HStack justify="space-between">
                <Heading size="md">My Class Assignments</Heading>
                <Button 
                  leftIcon={<Icon as={FaPlus} />} 
                  colorScheme="blue" 
                  size="sm"
                  onClick={() => navigate('/teacher/classes/new')}
                >
                  Request Assignment
                </Button>
              </HStack>
              
              <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }} gap={6}>
                {assignments.map((assignment) => (
                  <Card key={assignment.id} bg={cardBg} cursor="pointer" 
                        onClick={() => navigate(`/teacher/classes/${assignment.class_name}/${assignment.subject_code}`)}>
                    <CardHeader pb={2}>
                      <HStack justify="space-between">
                        <Badge colorScheme={assignment.is_primary ? "purple" : "blue"} variant="solid">
                          {assignment.is_primary ? "Form Teacher" : "Subject Teacher"}
                        </Badge>
                        <Icon as={FaChalkboardTeacher} color="blue.500" />
                      </HStack>
                    </CardHeader>
                    <CardBody pt={0}>
                      <VStack align="start" spacing={2}>
                        <Heading size="sm" color="blue.600">
                          {assignment.class_name}
                        </Heading>
                        <Text fontWeight="medium">
                          {assignment.subject_name}
                        </Text>
                        <Text fontSize="sm" color="gray.600">
                          Code: {assignment.subject_code}
                        </Text>
                        <HStack>
                          <Icon as={FaUsers} size="sm" />
                          <Text fontSize="sm">{assignment.student_count} students</Text>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </Grid>
            </VStack>
          </TabPanel>

          {/* Grade Management Tab */}
          <TabPanel>
            <VStack align="stretch" spacing={6}>
              <HStack justify="space-between">
                <Heading size="md">Grade Management</Heading>
                <Button 
                  leftIcon={<Icon as={FaClipboardList} />} 
                  colorScheme="green" 
                  size="sm"
                  onClick={() => navigate('/teacher/grades')}
                >
                  Manage All Grades
                </Button>
              </HStack>
              
              {statistics.pending_grades > 0 && (
                <Alert status="warning" borderRadius="md">
                  <AlertIcon />
                  You have {statistics.pending_grades} pending grades to submit
                </Alert>
              )}

              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                {assignments.slice(0, 4).map((assignment) => (
                  <Card key={assignment.id} bg={cardBg}>
                    <CardBody>
                      <VStack align="stretch" spacing={3}>
                        <HStack justify="space-between">
                          <Text fontWeight="bold">{assignment.class_name}</Text>
                          <Badge colorScheme="blue">{assignment.subject_code}</Badge>
                        </HStack>
                        <Text fontSize="sm" color="gray.600">
                          {assignment.subject_name}
                        </Text>
                        <HStack justify="space-between">
                          <Text fontSize="sm">{assignment.student_count} students</Text>
                          <Button 
                            size="sm" 
                            colorScheme="blue" 
                            variant="outline"
                            onClick={() => navigate(`/teacher/grades/${assignment.class_name}/${assignment.subject_code}`)}
                          >
                            Enter Grades
                          </Button>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            </VStack>
          </TabPanel>

          {/* Attendance Tab */}
          <TabPanel>
            <VStack align="stretch" spacing={6}>
              <HStack justify="space-between">
                <Heading size="md">Attendance Management</Heading>
                <Button 
                  leftIcon={<Icon as={FaCalendarCheck} />} 
                  colorScheme="purple" 
                  size="sm"
                  onClick={() => navigate('/teacher/attendance')}
                >
                  Take Attendance
                </Button>
              </HStack>

              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                {assignments.slice(0, 4).map((assignment) => (
                  <Card key={assignment.id} bg={cardBg}>
                    <CardBody>
                      <VStack align="stretch" spacing={3}>
                        <HStack justify="space-between">
                          <Text fontWeight="bold">{assignment.class_name}</Text>
                          <Badge colorScheme="purple">{assignment.subject_code}</Badge>
                        </HStack>
                        <Text fontSize="sm" color="gray.600">
                          {assignment.subject_name}
                        </Text>
                        <HStack justify="space-between">
                          <Text fontSize="sm">{assignment.student_count} students</Text>
                          <Button 
                            size="sm" 
                            colorScheme="purple" 
                            variant="outline"
                            onClick={() => navigate(`/teacher/attendance/${assignment.class_name}`)}
                          >
                            Mark Attendance
                          </Button>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            </VStack>
          </TabPanel>

          {/* Schedule Tab */}
          <TabPanel>
            <VStack align="stretch" spacing={6}>
              <Heading size="md">Today's Schedule</Heading>
              
              {upcoming_classes.length > 0 ? (
                <VStack align="stretch" spacing={4}>
                  {upcoming_classes.map((class_schedule, index) => (
                    <Card key={index} bg={cardBg}>
                      <CardBody>
                        <HStack spacing={4}>
                          <Box>
                            <Icon as={FaClock} color="blue.500" boxSize={5} />
                          </Box>
                          <VStack align="start" spacing={1} flex={1}>
                            <Text fontWeight="bold">{class_schedule.class_name}</Text>
                            <Text color="gray.600">{class_schedule.subject_name}</Text>
                            <HStack spacing={4}>
                              <Text fontSize="sm">
                                <strong>Time:</strong> {class_schedule.time}
                              </Text>
                              {class_schedule.room && (
                                <Text fontSize="sm">
                                  <strong>Room:</strong> {class_schedule.room}
                                </Text>
                              )}
                            </HStack>
                          </VStack>
                        </HStack>
                      </CardBody>
                    </Card>
                  ))}
                </VStack>
              ) : (
                <Card bg={cardBg}>
                  <CardBody>
                    <Text textAlign="center" color="gray.600">
                      No classes scheduled for today
                    </Text>
                  </CardBody>
                </Card>
              )}
            </VStack>
          </TabPanel>

          {/* Notifications Tab */}
          <TabPanel>
            <VStack align="stretch" spacing={6}>
              <Heading size="md">Notifications</Heading>
              
              {notifications.length > 0 ? (
                <VStack align="stretch" spacing={4}>
                  {notifications.map((notification) => (
                    <Alert 
                      key={notification.id} 
                      status={notification.type} 
                      borderRadius="md"
                    >
                      <AlertIcon />
                      <Box flex={1}>
                        <Text fontWeight="bold">{notification.title}</Text>
                        <Text>{notification.message}</Text>
                        <Text fontSize="sm" color="gray.600" mt={1}>
                          {new Date(notification.date).toLocaleDateString()}
                        </Text>
                      </Box>
                    </Alert>
                  ))}
                </VStack>
              ) : (
                <Card bg={cardBg}>
                  <CardBody>
                    <Text textAlign="center" color="gray.600">
                      No new notifications
                    </Text>
                  </CardBody>
                </Card>
              )}
            </VStack>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  )
}

export default TeacherDashboard
