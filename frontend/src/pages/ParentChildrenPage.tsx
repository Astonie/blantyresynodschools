import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardBody,
  Heading,
  VStack,
  HStack,
  Text,
  Avatar,
  Badge,
  Grid,
  GridItem,
  Button,
  Alert,
  AlertIcon,
  Spinner,
  Center,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Icon,
  Flex,
  Spacer,
  Divider,
  Progress,
  Tooltip
} from '@chakra-ui/react'
import {
  FaUser,
  FaGraduationCap,
  FaCalendarAlt,
  FaEye,
  FaComments,
  FaChartLine,
  FaInfoCircle,
  FaBirthdayCake
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
  gender?: string
  email?: string
}

interface ChildSummary extends Child {
  gpa?: number
  average_percentage?: number
  total_subjects?: number
  unread_communications?: number
  last_activity?: string
  attendance_percentage?: number
}

export function ParentChildrenPage() {
  const navigate = useNavigate()
  const [children, setChildren] = useState<ChildSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchChildrenData = async () => {
      try {
        setLoading(true)
        console.log('Fetching children data...')
        
        // Fetch children basic info
        const childrenResponse = await api.get('/parents/children')
        const childrenData = childrenResponse.data || []
        console.log('Children received:', childrenData)

        // Fetch additional data for each child
        const enhancedChildren = await Promise.all(
          childrenData.map(async (child: Child) => {
            try {
              // Get academic report card
              const reportResponse = await api.get(`/parents/children/${child.id}/report-card`, {
                params: {
                  academic_year: '2024',
                  term: 'Term 1 Final'
                }
              })
              const reportData = reportResponse.data || {}
              console.log(`Report card for child ${child.id}:`, reportData)

              // Communications count - placeholder since API doesn't exist yet
              const unreadCount = 0

              return {
                ...child,
                gpa: reportData.overall_gpa || 0,
                average_percentage: reportData.term_average || 0,
                total_subjects: reportData.total_subjects || 0,
                unread_communications: unreadCount,
                last_activity: new Date().toISOString(),
                attendance_percentage: 85 // Placeholder since we don't have attendance API
              }

            } catch (error) {
              console.error(`Error fetching data for child ${child.id}:`, error)
              // Return child with default values if academic data fails
              return {
                ...child,
                gpa: 0,
                average_percentage: 0,
                total_subjects: 0,
                unread_communications: 0,
                last_activity: null,
                attendance_percentage: 0
              }
            }
          })
        )

        setChildren(enhancedChildren)
        console.log('Enhanced children data:', enhancedChildren)
      } catch (err: any) {
        console.error('Error fetching children:', err)
        setError(err.response?.data?.detail || 'Failed to load children information')
      } finally {
        setLoading(false)
      }
    }

    fetchChildrenData()
  }, [])

  if (loading) {
    return (
      <Center h="400px">
        <VStack>
          <Spinner size="lg" color="blue.500" />
          <Text>Loading your children...</Text>
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
      </Box>
    )
  }

  if (children.length === 0) {
    return (
      <Box p={6}>
        <Alert status="info">
          <AlertIcon />
          No children found. Please contact the school administration if this seems incorrect.
        </Alert>
      </Box>
    )
  }

  // Calculate overall statistics
  const totalUnreadComms = children.reduce((sum, child) => sum + (child.unread_communications || 0), 0)
  const averageGPA = children.length > 0 
    ? (children.reduce((sum, child) => sum + (child.gpa || 0), 0) / children.length).toFixed(2)
    : '0.00'
  const totalSubjects = children.reduce((sum, child) => sum + (child.total_subjects || 0), 0)

  return (
    <Box p={6}>
      {/* Page Header */}
      <VStack align="stretch" spacing={6} mb={8}>
        <Heading size="lg" color="blue.600">
          My Children
        </Heading>
        
        {/* Overview Statistics */}
        <SimpleGrid columns={{ base: 1, md: 3, lg: 4 }} spacing={6}>
          <Card>
            <CardBody>
              <Stat>
                <StatLabel>Total Children</StatLabel>
                <StatNumber color="blue.600">{children.length}</StatNumber>
                <StatHelpText>Enrolled in school</StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <Stat>
                <StatLabel>Average GPA</StatLabel>
                <StatNumber color="green.600">{averageGPA}</StatNumber>
                <StatHelpText>Across all children</StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <Stat>
                <StatLabel>Total Subjects</StatLabel>
                <StatNumber color="purple.600">{totalSubjects}</StatNumber>
                <StatHelpText>Combined enrollment</StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <Stat>
                <StatLabel>Unread Messages</StatLabel>
                <StatNumber color="orange.600">{totalUnreadComms}</StatNumber>
                <StatHelpText>
                  <Text color={totalUnreadComms > 0 ? "red.500" : "gray.500"}>
                    {totalUnreadComms > 0 ? 'Action needed' : 'All caught up'}
                  </Text>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>
      </VStack>

      {/* Children Cards */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
        {children.map((child) => (
          <Card key={child.id} shadow="md" _hover={{ shadow: 'lg' }} transition="all 0.2s">
            <CardBody>
              <VStack align="stretch" spacing={4}>
                {/* Child Header */}
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
                    <HStack spacing={3} wrap="wrap">
                      <Badge colorScheme="blue" fontSize="sm">
                        {child.admission_no}
                      </Badge>
                      <Text fontSize="sm" color="gray.600">
                        <Icon as={FaGraduationCap} mr={1} />
                        {child.class_name || 'No Class'}
                      </Text>
                      <Badge 
                        colorScheme={child.status === 'active' ? 'green' : 'gray'}
                        fontSize="sm"
                      >
                        {child.status?.toUpperCase() || 'ACTIVE'}
                      </Badge>
                    </HStack>
                  </VStack>
                  {child.unread_communications && child.unread_communications > 0 && (
                    <Tooltip label={`${child.unread_communications} unread messages`}>
                      <Badge colorScheme="red" borderRadius="full" px={2}>
                        {child.unread_communications}
                      </Badge>
                    </Tooltip>
                  )}
                </HStack>

                <Divider />

                {/* Academic Summary */}
                <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                  <VStack align="start" spacing={2}>
                    <Text fontSize="sm" color="gray.600" fontWeight="medium">
                      Academic Performance
                    </Text>
                    {child.gpa ? (
                      <HStack>
                        <Text fontSize="lg" fontWeight="bold" color="green.600">
                          GPA: {child.gpa.toFixed(2)}
                        </Text>
                        {child.average_percentage && (
                          <Text fontSize="sm" color="gray.500">
                            ({child.average_percentage.toFixed(1)}%)
                          </Text>
                        )}
                      </HStack>
                    ) : (
                      <Text fontSize="sm" color="gray.500">No academic data yet</Text>
                    )}
                    
                    {(child.total_subjects || 0) > 0 && (
                      <Text fontSize="sm" color="gray.600">
                        Enrolled in {child.total_subjects} subject{child.total_subjects !== 1 ? 's' : ''}
                      </Text>
                    )}
                  </VStack>

                  <VStack align="start" spacing={2}>
                    <Text fontSize="sm" color="gray.600" fontWeight="medium">
                      Attendance
                    </Text>
                    <VStack align="start" spacing={1}>
                      <Progress 
                        value={child.attendance_percentage || 0} 
                        colorScheme={
                          (child.attendance_percentage || 0) >= 95 ? 'green' :
                          (child.attendance_percentage || 0) >= 85 ? 'yellow' : 'red'
                        }
                        size="sm"
                        w="80px"
                      />
                      <Text fontSize="sm" fontWeight="medium">
                        {child.attendance_percentage || 0}%
                      </Text>
                    </VStack>
                  </VStack>
                </Grid>

                {/* Child Information */}
                {(child.date_of_birth || child.enrollment_date || child.email) && (
                  <>
                    <Divider />
                    <VStack align="start" spacing={2}>
                      <Text fontSize="sm" color="gray.600" fontWeight="medium">
                        Information
                      </Text>
                      <VStack align="start" spacing={1}>
                        {child.date_of_birth && (
                          <HStack>
                            <Icon as={FaBirthdayCake} color="pink.500" />
                            <Text fontSize="sm">
                              Born: {new Date(child.date_of_birth).toLocaleDateString()}
                            </Text>
                          </HStack>
                        )}
                        {child.enrollment_date && (
                          <HStack>
                            <Icon as={FaCalendarAlt} color="blue.500" />
                            <Text fontSize="sm">
                              Enrolled: {new Date(child.enrollment_date).toLocaleDateString()}
                            </Text>
                          </HStack>
                        )}
                        {child.email && (
                          <HStack>
                            <Icon as={FaUser} color="gray.500" />
                            <Text fontSize="sm">{child.email}</Text>
                          </HStack>
                        )}
                      </VStack>
                    </VStack>
                  </>
                )}

                <Divider />

                {/* Action Buttons */}
                <HStack justify="space-between" wrap="wrap" spacing={2}>
                  <Button
                    leftIcon={<FaEye />}
                    colorScheme="blue"
                    variant="solid"
                    size="sm"
                    onClick={() => navigate(`/parent/child/${child.id}`)}
                  >
                    View Details
                  </Button>
                  
                  <HStack spacing={2}>
                    <Button
                      leftIcon={<FaChartLine />}
                      colorScheme="green"
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/parent/child/${child.id}?tab=academic`)}
                    >
                      Academic
                    </Button>
                    
                    <Button
                      leftIcon={<FaComments />}
                      colorScheme="orange"
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/parent/communications?child=${child.id}`)}
                      position="relative"
                    >
                      Messages
                      {child.unread_communications && child.unread_communications > 0 && (
                        <Badge
                          position="absolute"
                          top="-8px"
                          right="-8px"
                          colorScheme="red"
                          borderRadius="full"
                          fontSize="xs"
                          minW="18px"
                          h="18px"
                        >
                          {child.unread_communications > 9 ? '9+' : child.unread_communications}
                        </Badge>
                      )}
                    </Button>
                  </HStack>
                </HStack>

                {/* Last Activity */}
                {child.last_activity && (
                  <Text fontSize="xs" color="gray.500" textAlign="center">
                    Last activity: {new Date(child.last_activity).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </Text>
                )}
              </VStack>
            </CardBody>
          </Card>
        ))}
      </SimpleGrid>

      {/* Quick Actions */}
      <Card mt={8}>
        <CardBody>
          <VStack spacing={4}>
            <Heading size="md" color="blue.600">Quick Actions</Heading>
            <HStack spacing={4} wrap="wrap" justify="center">
              <Button
                leftIcon={<FaComments />}
                colorScheme="blue"
                onClick={() => navigate('/parent/communications')}
              >
                All Communications ({totalUnreadComms})
              </Button>
              <Button
                leftIcon={<FaChartLine />}
                colorScheme="green"
                onClick={() => navigate('/parent/academic')}
              >
                Academic Overview
              </Button>
              <Button
                leftIcon={<FaInfoCircle />}
                colorScheme="gray"
                variant="outline"
                onClick={() => navigate('/parent/settings')}
              >
                Settings
              </Button>
            </HStack>
          </VStack>
        </CardBody>
      </Card>
    </Box>
  )
}
