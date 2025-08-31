import React, { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  Text,
  Card,
  CardBody,
  CardHeader,
  Badge,
  Button,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Avatar,
  Grid,
  GridItem,
  Alert,
  AlertIcon,
  Spinner,
  Center,
  Divider,
  Icon,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Progress,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Flex
} from '@chakra-ui/react'
import { FaChild, FaGraduationCap, FaComments, FaCalendar, FaTrophy, FaBook } from 'react-icons/fa'
import { useAuth } from '../lib/auth'
import { api } from '../lib/api'

interface Child {
  id: number
  first_name: string
  last_name: string
  admission_no: string
  class_name?: string
  profile_photo?: string
}

interface ReportCard {
  student_id: number
  student_name: string
  class_name: string
  academic_year: string
  term: string
  subjects: Array<{
    subject_name: string
    ca_score: number
    exam_score: number
    overall_score: number
    grade: string
    grade_points: number
  }>
  overall_gpa: number
  total_subjects: number
  term_average: number
}

interface Communication {
  id: number
  title: string
  message: string
  type: 'announcement' | 'event' | 'notice' | 'urgent'
  date: string
  is_read: boolean
  targeted_roles?: string[]
}

export default function ParentDashboard() {
  const { user } = useAuth()
  const [children, setChildren] = useState<Child[]>([])
  const [selectedChild, setSelectedChild] = useState<Child | null>(null)
  const [reportCard, setReportCard] = useState<ReportCard | null>(null)
  const [communications, setCommunications] = useState<Communication[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState(0)

  // Load parent's children
  useEffect(() => {
    const fetchChildren = async () => {
      try {
        const response = await api.get('/parents/children')
        const childrenData = response.data
        setChildren(childrenData)
        if (childrenData.length > 0) {
          setSelectedChild(childrenData[0])
        }
      } catch (error) {
        console.error('Error fetching children:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchChildren()
  }, [])

  // Load communications
  useEffect(() => {
    const fetchCommunications = async () => {
      try {
        const response = await api.get('/communications', {
          params: { role: 'parent', limit: 20 }
        })
        setCommunications(response.data || [])
      } catch (error) {
        console.error('Error fetching communications:', error)
      }
    }

    fetchCommunications()
  }, [])

  // Load selected child's report card
  useEffect(() => {
    if (selectedChild) {
      const fetchReportCard = async () => {
        try {
          const response = await api.get(`/parents/children/${selectedChild.id}/report-card`)
          setReportCard(response.data)
        } catch (error) {
          console.error('Error fetching report card:', error)
          setReportCard(null)
        }
      }

      fetchReportCard()
    }
  }, [selectedChild])

  const getCommunicationIcon = (type: string) => {
    switch (type) {
      case 'urgent': return { icon: FaComments, color: 'red.500' }
      case 'event': return { icon: FaCalendar, color: 'blue.500' }
      case 'announcement': return { icon: FaGraduationCap, color: 'green.500' }
      default: return { icon: FaComments, color: 'gray.500' }
    }
  }

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'green'
      case 'B': return 'blue'
      case 'C': return 'yellow'
      case 'D': return 'orange'
      case 'F': return 'red'
      default: return 'gray'
    }
  }

  if (loading) {
    return (
      <Center h="400px">
        <VStack>
          <Spinner size="xl" color="blue.500" />
          <Text>Loading your children's information...</Text>
        </VStack>
      </Center>
    )
  }

  if (children.length === 0) {
    return (
      <Center h="400px">
        <Alert status="info" maxW="400px">
          <AlertIcon />
          <VStack align="start">
            <Text fontWeight="bold">No Children Found</Text>
            <Text>No student records are linked to your parent account. Please contact the school administration.</Text>
          </VStack>
        </Alert>
      </Center>
    )
  }

  return (
    <Box p={6} maxW="1200px" mx="auto">
      {/* Header */}
      <VStack align="stretch" spacing={6}>
        <Box>
          <Text fontSize="2xl" fontWeight="bold" color="blue.600" mb={2}>
            Parent Portal
          </Text>
          <Text color="gray.600">
            Welcome back, {user?.full_name || user?.email}
          </Text>
        </Box>

        {/* Children Selector */}
        <Card>
          <CardHeader pb={2}>
            <HStack>
              <Icon as={FaChild} color="blue.500" />
              <Text fontWeight="bold">My Children</Text>
            </HStack>
          </CardHeader>
          <CardBody>
            <HStack spacing={4} flexWrap="wrap">
              {children.map((child) => (
                <Button
                  key={child.id}
                  variant={selectedChild?.id === child.id ? 'solid' : 'outline'}
                  colorScheme="blue"
                  onClick={() => setSelectedChild(child)}
                  leftIcon={<Avatar size="sm" name={`${child.first_name} ${child.last_name}`} />}
                >
                  <VStack spacing={0} align="start">
                    <Text fontSize="sm" fontWeight="bold">
                      {child.first_name} {child.last_name}
                    </Text>
                    <Text fontSize="xs" color="gray.500">
                      {child.admission_no} • {child.class_name || 'No Class'}
                    </Text>
                  </VStack>
                </Button>
              ))}
            </HStack>
          </CardBody>
        </Card>

        {/* Main Content Tabs */}
        {selectedChild && (
          <Tabs index={activeTab} onChange={setActiveTab} colorScheme="blue">
            <TabList>
              <Tab>
                <HStack>
                  <Icon as={FaTrophy} />
                  <Text>Academic Progress</Text>
                </HStack>
              </Tab>
              <Tab>
                <HStack>
                  <Icon as={FaComments} />
                  <Text>Communications</Text>
                  {communications.filter(c => !c.is_read).length > 0 && (
                    <Badge colorScheme="red" borderRadius="full">
                      {communications.filter(c => !c.is_read).length}
                    </Badge>
                  )}
                </HStack>
              </Tab>
            </TabList>

            <TabPanels>
              {/* Academic Progress Tab */}
              <TabPanel>
                <VStack align="stretch" spacing={6}>
                  {/* Academic Summary */}
                  <Card>
                    <CardHeader>
                      <HStack>
                        <Icon as={FaGraduationCap} color="green.500" />
                        <Text fontWeight="bold">Academic Summary</Text>
                        <Badge colorScheme="blue">{selectedChild.class_name || 'No Class'}</Badge>
                      </HStack>
                    </CardHeader>
                    <CardBody>
                      {reportCard ? (
                        <Grid templateColumns="repeat(4, 1fr)" gap={4}>
                          <Stat>
                            <StatLabel>Overall GPA</StatLabel>
                            <StatNumber color="blue.600">{reportCard.overall_gpa.toFixed(2)}</StatNumber>
                          </Stat>
                          <Stat>
                            <StatLabel>Total Subjects</StatLabel>
                            <StatNumber>{reportCard.total_subjects}</StatNumber>
                          </Stat>
                          <Stat>
                            <StatLabel>Term Average</StatLabel>
                            <StatNumber>{reportCard.term_average.toFixed(1)}%</StatNumber>
                          </Stat>
                          <Stat>
                            <StatLabel>Academic Year</StatLabel>
                            <StatNumber fontSize="lg">{reportCard.academic_year}</StatNumber>
                          </Stat>
                        </Grid>
                      ) : (
                        <Alert status="info">
                          <AlertIcon />
                          No academic records available for this student yet.
                        </Alert>
                      )}
                    </CardBody>
                  </Card>

                  {/* Subject Performance */}
                  {reportCard && reportCard.subjects && reportCard.subjects.length > 0 && (
                    <Card>
                      <CardHeader>
                        <HStack justify="space-between">
                          <HStack>
                            <Icon as={FaBook} color="purple.500" />
                            <Text fontWeight="bold">Subject Performance - {reportCard.term}</Text>
                          </HStack>
                          <Badge colorScheme="purple">{reportCard.academic_year}</Badge>
                        </HStack>
                      </CardHeader>
                      <CardBody>
                        <Box overflowX="auto">
                          <Table variant="simple">
                            <Thead>
                              <Tr>
                                <Th>Subject</Th>
                                <Th textAlign="center">CA Score</Th>
                                <Th textAlign="center">Exam Score</Th>
                                <Th textAlign="center">Total</Th>
                                <Th textAlign="center">Grade</Th>
                                <Th textAlign="center">Performance</Th>
                              </Tr>
                            </Thead>
                            <Tbody>
                              {reportCard.subjects.map((subject, index) => (
                                <Tr key={index}>
                                  <Td fontWeight="medium">{subject.subject_name}</Td>
                                  <Td textAlign="center">
                                    <Badge variant="outline" colorScheme="blue">
                                      {subject.ca_score}/30
                                    </Badge>
                                  </Td>
                                  <Td textAlign="center">
                                    <Badge variant="outline" colorScheme="green">
                                      {subject.exam_score}/70
                                    </Badge>
                                  </Td>
                                  <Td textAlign="center">
                                    <Text fontWeight="bold">
                                      {subject.overall_score}/100
                                    </Text>
                                  </Td>
                                  <Td textAlign="center">
                                    <Badge colorScheme={getGradeColor(subject.grade)} size="lg">
                                      {subject.grade}
                                    </Badge>
                                  </Td>
                                  <Td textAlign="center">
                                    <Progress
                                      value={subject.overall_score}
                                      colorScheme={getGradeColor(subject.grade)}
                                      size="lg"
                                      borderRadius="md"
                                      w="80px"
                                    />
                                  </Td>
                                </Tr>
                              ))}
                            </Tbody>
                          </Table>
                        </Box>
                      </CardBody>
                    </Card>
                  )}
                </VStack>
              </TabPanel>

              {/* Communications Tab */}
              <TabPanel>
                <VStack align="stretch" spacing={4}>
                  {communications.length > 0 ? (
                    communications.map((comm) => {
                      const iconInfo = getCommunicationIcon(comm.type)
                      return (
                        <Card
                          key={comm.id}
                          variant={comm.is_read ? 'outline' : 'elevated'}
                          borderLeft={comm.is_read ? 'none' : '4px solid'}
                          borderLeftColor={iconInfo.color}
                        >
                          <CardBody>
                            <HStack justify="space-between" align="start" mb={3}>
                              <HStack>
                                <Icon as={iconInfo.icon} color={iconInfo.color} />
                                <VStack align="start" spacing={1}>
                                  <Text fontWeight="bold" fontSize="md">
                                    {comm.title}
                                  </Text>
                                  <HStack>
                                    <Badge
                                      colorScheme={
                                        comm.type === 'urgent' ? 'red' :
                                        comm.type === 'event' ? 'blue' :
                                        comm.type === 'announcement' ? 'green' : 'gray'
                                      }
                                      textTransform="capitalize"
                                    >
                                      {comm.type}
                                    </Badge>
                                    <Text fontSize="sm" color="gray.500">
                                      {new Date(comm.date).toLocaleDateString('en-US', {
                                        year: 'numeric',
                                        month: 'short',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                      })}
                                    </Text>
                                  </HStack>
                                </VStack>
                              </HStack>
                              {!comm.is_read && (
                                <Badge colorScheme="blue" variant="solid">
                                  New
                                </Badge>
                              )}
                            </HStack>
                            <Text color="gray.700" lineHeight="1.6">
                              {comm.message}
                            </Text>
                          </CardBody>
                        </Card>
                      )
                    })
                  ) : (
                    <Center py={8}>
                      <VStack>
                        <Icon as={FaComments} size="48px" color="gray.300" />
                        <Text color="gray.500" textAlign="center">
                          No communications available at this time.
                        </Text>
                      </VStack>
                    </Center>
                  )}
                </VStack>
              </TabPanel>
            </TabPanels>
          </Tabs>
        )}
      </VStack>
    </Box>
  )
}
