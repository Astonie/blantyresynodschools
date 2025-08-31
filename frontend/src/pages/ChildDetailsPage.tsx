import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Text,
  Avatar,
  Badge,
  Grid,
  GridItem,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Progress,
  Divider,
  Alert,
  AlertIcon,
  Button,
  Spinner,
  Center,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  SimpleGrid,
  List,
  ListItem,
  ListIcon,
  Icon,
  Flex,
  Spacer
} from '@chakra-ui/react'
import {
  FaGraduationCap,
  FaBookOpen,
  FaChartLine,
  FaCalendarAlt,
  FaComments,
  FaTrophy,
  FaExclamationTriangle,
  FaCheckCircle,
  FaUser
} from 'react-icons/fa'
import { api } from '../lib/api'

interface Child {
  id: number
  first_name: string
  last_name: string
  admission_no: string
  class_name?: string
  date_of_birth?: string
  enrollment_date?: string
  status?: string
}

interface AcademicRecord {
  subject: string
  grade: string
  marks: number
  total_marks: number
  percentage: number
  grade_points: number
  teacher_comment?: string
  term: string
  year: number
}

interface Communication {
  id: number
  title: string
  content: string
  type: 'announcement' | 'notification' | 'urgent' | 'general'
  created_at: string
  read_status: boolean
  priority: 'low' | 'medium' | 'high'
}

export function ChildDetailsPage() {
  const { childId } = useParams<{ childId: string }>()
  const navigate = useNavigate()
  const [child, setChild] = useState<Child | null>(null)
  const [academicRecords, setAcademicRecords] = useState<AcademicRecord[]>([])
  const [communications, setCommunications] = useState<Communication[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchChildData = async () => {
      if (!childId) return

      try {
        setLoading(true)
        
        // Fetch child details
        const childResponse = await api.get(`/parents/children/${childId}`)
        setChild(childResponse.data)

        // Fetch academic records
        const academicResponse = await api.get(`/students/${childId}/academic-records`)
        setAcademicRecords(academicResponse.data || [])

        // Fetch child-specific communications
        const commResponse = await api.get('/communications', {
          params: { child_id: childId }
        })
        setCommunications(commResponse.data || [])

      } catch (err: any) {
        console.error('Error fetching child data:', err)
        setError(err.response?.data?.detail || 'Failed to load child information')
      } finally {
        setLoading(false)
      }
    }

    fetchChildData()
  }, [childId])

  if (loading) {
    return (
      <Center h="400px">
        <VStack>
          <Spinner size="lg" color="blue.500" />
          <Text>Loading child information...</Text>
        </VStack>
      </Center>
    )
  }

  if (error) {
    return (
      <Box p={6}>
        <Alert status="error">
          <AlertIcon />
          {error}
        </Alert>
        <Button mt={4} onClick={() => navigate('/app/parent/children')}>
          Back to My Children
        </Button>
      </Box>
    )
  }

  if (!child) {
    return (
      <Box p={6}>
        <Alert status="warning">
          <AlertIcon />
          Child not found or you don't have permission to view this child's information.
        </Alert>
        <Button mt={4} onClick={() => navigate('/app/parent/children')}>
          Back to My Children
        </Button>
      </Box>
    )
  }

  // Calculate academic statistics
  const currentTermRecords = academicRecords.filter(r => 
    r.term === 'Term 3' && r.year === new Date().getFullYear()
  )
  
  const overallGPA = currentTermRecords.length > 0 
    ? (currentTermRecords.reduce((sum, r) => sum + r.grade_points, 0) / currentTermRecords.length).toFixed(2)
    : 'N/A'

  const averagePercentage = currentTermRecords.length > 0
    ? (currentTermRecords.reduce((sum, r) => sum + r.percentage, 0) / currentTermRecords.length).toFixed(1)
    : 0

  const unreadComms = communications.filter(c => !c.read_status).length

  return (
    <Box p={6}>
      {/* Child Header */}
      <Card mb={6}>
        <CardBody>
          <HStack spacing={4} align="center">
            <Avatar 
              size="lg" 
              name={`${child.first_name} ${child.last_name}`}
              bg="blue.500"
            />
            <VStack align="start" spacing={1} flex={1}>
              <Heading size="md" color="blue.600">
                {child.first_name} {child.last_name}
              </Heading>
              <HStack spacing={4} wrap="wrap">
                <Badge colorScheme="blue" fontSize="sm">
                  {child.admission_no}
                </Badge>
                <Text fontSize="sm" color="gray.600">
                  <Icon as={FaUser} mr={1} />
                  {child.class_name || 'No Class Assigned'}
                </Text>
                <Badge 
                  colorScheme={child.status === 'active' ? 'green' : 'gray'}
                  fontSize="sm"
                >
                  {child.status?.toUpperCase() || 'ACTIVE'}
                </Badge>
              </HStack>
            </VStack>
            <Button 
              leftIcon={<FaComments />}
              colorScheme="blue"
              variant="outline"
              onClick={() => navigate(`/app/parent/communications?child=${child.id}`)}
            >
              View Communications ({unreadComms})
            </Button>
          </HStack>
        </CardBody>
      </Card>

      {/* Overview Cards */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Current GPA</StatLabel>
              <StatNumber color="blue.600">{overallGPA}</StatNumber>
              <StatHelpText>
                <StatArrow type="increase" />
                Current Term
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Average Score</StatLabel>
              <StatNumber color="green.600">{averagePercentage}%</StatNumber>
              <StatHelpText>
                Across all subjects
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Subjects</StatLabel>
              <StatNumber color="purple.600">{currentTermRecords.length}</StatNumber>
              <StatHelpText>
                Currently enrolled
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Communications</StatLabel>
              <StatNumber color="orange.600">{communications.length}</StatNumber>
              <StatHelpText>
                <Text color="red.500" as="span">{unreadComms} unread</Text>
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Detailed Information Tabs */}
      <Tabs variant="enclosed" colorScheme="blue">
        <TabList>
          <Tab>
            <Icon as={FaGraduationCap} mr={2} />
            Academic Progress
          </Tab>
          <Tab>
            <Icon as={FaComments} mr={2} />
            Communications
            {unreadComms > 0 && (
              <Badge ml={2} colorScheme="red" fontSize="xs">
                {unreadComms}
              </Badge>
            )}
          </Tab>
          <Tab>
            <Icon as={FaChartLine} mr={2} />
            Performance Trends
          </Tab>
        </TabList>

        <TabPanels>
          {/* Academic Progress Tab */}
          <TabPanel>
            <VStack spacing={6} align="stretch">
              {currentTermRecords.length > 0 ? (
                currentTermRecords.map((record, index) => (
                  <Card key={index}>
                    <CardHeader>
                      <Flex align="center">
                        <HStack>
                          <Icon as={FaBookOpen} color="blue.500" />
                          <Heading size="sm">{record.subject}</Heading>
                        </HStack>
                        <Spacer />
                        <Badge
                          colorScheme={
                            record.percentage >= 80 ? 'green' :
                            record.percentage >= 60 ? 'yellow' : 'red'
                          }
                          fontSize="md"
                          px={3}
                          py={1}
                        >
                          {record.grade}
                        </Badge>
                      </Flex>
                    </CardHeader>
                    <CardBody>
                      <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
                        <VStack align="start" spacing={2}>
                          <Text fontSize="sm" color="gray.600">Marks Obtained</Text>
                          <Text fontSize="lg" fontWeight="bold">
                            {record.marks} / {record.total_marks}
                          </Text>
                          <Progress 
                            value={record.percentage} 
                            colorScheme={
                              record.percentage >= 80 ? 'green' :
                              record.percentage >= 60 ? 'yellow' : 'red'
                            }
                            w="full"
                          />
                          <Text fontSize="sm" color="gray.500">
                            {record.percentage.toFixed(1)}%
                          </Text>
                        </VStack>
                        
                        <VStack align="start" spacing={2}>
                          <Text fontSize="sm" color="gray.600">Grade Points</Text>
                          <Text fontSize="lg" fontWeight="bold" color="blue.600">
                            {record.grade_points.toFixed(1)}
                          </Text>
                        </VStack>
                      </Grid>

                      {record.teacher_comment && (
                        <>
                          <Divider my={4} />
                          <Box>
                            <Text fontSize="sm" color="gray.600" mb={2}>
                              Teacher's Comment:
                            </Text>
                            <Text fontSize="sm" fontStyle="italic">
                              "{record.teacher_comment}"
                            </Text>
                          </Box>
                        </>
                      )}
                    </CardBody>
                  </Card>
                ))
              ) : (
                <Alert status="info">
                  <AlertIcon />
                  No academic records available for the current term.
                </Alert>
              )}
            </VStack>
          </TabPanel>

          {/* Communications Tab */}
          <TabPanel>
            <VStack spacing={4} align="stretch">
              {communications.length > 0 ? (
                communications.slice(0, 10).map((comm) => (
                  <Card 
                    key={comm.id} 
                    bg={comm.read_status ? 'white' : 'blue.50'}
                    borderLeft={comm.read_status ? 'none' : '4px solid'}
                    borderLeftColor="blue.500"
                  >
                    <CardBody>
                      <HStack align="start" spacing={3}>
                        <Icon 
                          as={
                            comm.type === 'urgent' ? FaExclamationTriangle :
                            comm.type === 'announcement' ? FaTrophy :
                            FaComments
                          }
                          color={
                            comm.priority === 'high' ? 'red.500' :
                            comm.priority === 'medium' ? 'orange.500' :
                            'blue.500'
                          }
                          mt={1}
                        />
                        <VStack align="start" spacing={2} flex={1}>
                          <HStack justify="space-between" w="full">
                            <Heading size="sm" color="gray.800">
                              {comm.title}
                            </Heading>
                            <HStack spacing={2}>
                              {!comm.read_status && (
                                <Badge colorScheme="red" size="sm">NEW</Badge>
                              )}
                              <Badge 
                                colorScheme={
                                  comm.priority === 'high' ? 'red' :
                                  comm.priority === 'medium' ? 'orange' : 'gray'
                                }
                                size="sm"
                              >
                                {comm.priority.toUpperCase()}
                              </Badge>
                            </HStack>
                          </HStack>
                          <Text fontSize="sm" color="gray.600" noOfLines={3}>
                            {comm.content}
                          </Text>
                          <Text fontSize="xs" color="gray.500">
                            {new Date(comm.created_at).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </Text>
                        </VStack>
                      </HStack>
                    </CardBody>
                  </Card>
                ))
              ) : (
                <Alert status="info">
                  <AlertIcon />
                  No communications available for this child.
                </Alert>
              )}
              
              {communications.length > 10 && (
                <Button 
                  variant="outline" 
                  onClick={() => navigate(`/app/parent/communications?child=${child.id}`)}
                >
                  View All Communications ({communications.length})
                </Button>
              )}
            </VStack>
          </TabPanel>

          {/* Performance Trends Tab */}
          <TabPanel>
            <VStack spacing={6} align="stretch">
              <Card>
                <CardHeader>
                  <Heading size="md">Performance Overview</Heading>
                </CardHeader>
                <CardBody>
                  {currentTermRecords.length > 0 ? (
                    <VStack spacing={4} align="stretch">
                      {currentTermRecords
                        .sort((a, b) => b.percentage - a.percentage)
                        .map((record, index) => (
                          <HStack key={index} justify="space-between">
                            <Text fontWeight="medium">{record.subject}</Text>
                            <HStack>
                              <Progress 
                                value={record.percentage} 
                                w="100px"
                                colorScheme={
                                  record.percentage >= 80 ? 'green' :
                                  record.percentage >= 60 ? 'yellow' : 'red'
                                }
                              />
                              <Text fontSize="sm" w="50px" textAlign="right">
                                {record.percentage.toFixed(1)}%
                              </Text>
                              <Badge colorScheme="blue">{record.grade}</Badge>
                            </HStack>
                          </HStack>
                        ))}
                    </VStack>
                  ) : (
                    <Alert status="info">
                      <AlertIcon />
                      No performance data available yet.
                    </Alert>
                  )}
                </CardBody>
              </Card>

              {/* Performance Insights */}
              <Card>
                <CardHeader>
                  <Heading size="md">Insights & Recommendations</Heading>
                </CardHeader>
                <CardBody>
                  <List spacing={3}>
                    {currentTermRecords.filter(r => r.percentage >= 80).length > 0 && (
                      <ListItem>
                        <ListIcon as={FaCheckCircle} color="green.500" />
                        <Text as="span">
                          Excellent performance in {currentTermRecords.filter(r => r.percentage >= 80).length} subject(s)
                        </Text>
                      </ListItem>
                    )}
                    {currentTermRecords.filter(r => r.percentage < 60).length > 0 && (
                      <ListItem>
                        <ListIcon as={FaExclamationTriangle} color="orange.500" />
                        <Text as="span">
                          Needs attention in {currentTermRecords.filter(r => r.percentage < 60).length} subject(s)
                        </Text>
                      </ListItem>
                    )}
                    {parseFloat(overallGPA) >= 3.5 && (
                      <ListItem>
                        <ListIcon as={FaTrophy} color="yellow.500" />
                        <Text as="span">
                          Outstanding overall GPA of {overallGPA}
                        </Text>
                      </ListItem>
                    )}
                  </List>
                </CardBody>
              </Card>
            </VStack>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  )
}
