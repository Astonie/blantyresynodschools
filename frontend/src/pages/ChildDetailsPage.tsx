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
  FaUser,
  FaDownload
} from 'react-icons/fa'
import { api } from '../lib/api'
import { ReportCardPDFGenerator, getSchoolInfo } from '../services/reportCardService'

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
  subject_name: string
  ca_score: number
  exam_score: number
  overall_score: number
  grade: string | null
  grade_points: number
  is_finalized: boolean
}

interface ReportCard {
  student_id: number
  first_name: string
  last_name: string
  admission_no: string
  class_name: string
  academic_year: string
  term: string
  subjects: AcademicRecord[]
  total_subjects: number
  total_points: number
  gpa: number
  overall_gpa: number
  term_average: number
  class_position?: number
  total_students_in_class?: number
  attendance_percentage?: number
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
  const [reportCard, setReportCard] = useState<ReportCard | null>(null)
  const [communications, setCommunications] = useState<Communication[]>([])
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchChildData = async () => {
      if (!childId) return

      try {
        setLoading(true)
        console.log('Fetching data for child ID:', childId)
        
        // Fetch all children first to get basic info for this child
        const childrenResponse = await api.get('/parents/children')
        const allChildren = childrenResponse.data || []
        const selectedChild = allChildren.find((c: any) => c.id.toString() === childId)
        
        if (!selectedChild) {
          throw new Error('Child not found or access denied')
        }
        
        setChild(selectedChild)
        console.log('Child found:', selectedChild)

        // Fetch academic records (report card)
        try {
          const reportResponse = await api.get(`/parents/children/${childId}/report-card`, {
            params: {
              academic_year: '2024',
              term: 'Term 1 Final'
            }
          })
          setReportCard(reportResponse.data)
          console.log('Report card loaded:', reportResponse.data)
        } catch (reportError) {
          console.error('Error fetching report card:', reportError)
          // Don't fail the whole page if report card fails
        }

        // Communications placeholder - API not implemented yet
        setCommunications([])

      } catch (err: any) {
        console.error('Error fetching child data:', err)
        setError(err.response?.data?.detail || err.message || 'Failed to load child information')
      } finally {
        setLoading(false)
      }
    }

    fetchChildData()
  }, [childId])

  const handleDownloadReportCard = async () => {
    if (!child || !reportCard) return

    try {
      setDownloading(true)
      
      // Prepare data for PDF generation
      const pdfData = {
        student: {
          id: child.id,
          full_name: `${child.first_name} ${child.last_name}`,
          student_id: child.admission_no,
          class_name: child.class_name || 'Not Assigned'
        },
        academic_year: reportCard.academic_year,
        term: reportCard.term,
        subjects: reportCard.subjects.map(subject => ({
          subject: subject.subject_name || 'Unknown Subject',
          percentage: subject.overall_score || 0,
          grade: subject.grade || 'N/A',
          points: subject.grade_points || 0,
          teacher_comment: 'Good performance' // Placeholder
        })),
        overall_gpa: reportCard.overall_gpa,
        term_average: reportCard.term_average,
        total_subjects: reportCard.total_subjects,
        class_position: reportCard.class_position,
        total_students_in_class: reportCard.total_students_in_class,
        attendance_percentage: reportCard.attendance_percentage || 85,
        conduct_grade: 'A', // Placeholder
        teacher_remarks: `${child.first_name} has shown consistent effort throughout the term. Continue to maintain this standard.`,
        head_teacher_remarks: 'A dedicated student with good academic progress. Keep up the excellent work!'
      }

      // Generate PDF
      const schoolInfo = getSchoolInfo()
      const pdfGenerator = new ReportCardPDFGenerator(schoolInfo)
      pdfGenerator.generateReportCard(pdfData)
      
      // Download the PDF
      const filename = `${child.first_name}_${child.last_name}_Report_Card_${reportCard.academic_year}_${reportCard.term.replace(/\s+/g, '_')}.pdf`
      pdfGenerator.downloadPDF(filename)
      
    } catch (error) {
      console.error('Error generating report card:', error)
      // You might want to show a toast notification here
    } finally {
      setDownloading(false)
    }
  }

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
        <Button mt={4} onClick={() => navigate('/parent/children')}>
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
        <Button mt={4} onClick={() => navigate('/parent/children')}>
          Back to My Children
        </Button>
      </Box>
    )
  }

  // Calculate academic statistics
  const overallGPA = reportCard?.overall_gpa?.toFixed(2) || 'N/A'
  const averagePercentage = reportCard?.term_average?.toFixed(1) || '0'
  const totalSubjects = reportCard?.total_subjects || 0
  const unreadComms = communications.filter(c => !c.read_status).length
  
  // Extract current term records from report card
  const currentTermRecords = reportCard?.subjects || []

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
            <HStack spacing={3}>
              <Button 
                leftIcon={<FaDownload />}
                colorScheme="green"
                onClick={handleDownloadReportCard}
                isLoading={downloading}
                loadingText="Generating..."
              >
                Download Report Card
              </Button>
              <Button 
                leftIcon={<FaComments />}
                colorScheme="blue"
                variant="outline"
                onClick={() => navigate(`/parent/communications?child=${child.id}`)}
              >
                View Communications ({unreadComms})
              </Button>
            </HStack>
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
              <StatNumber color="purple.600">{totalSubjects}</StatNumber>
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
              {reportCard && reportCard.subjects && reportCard.subjects.length > 0 ? (
                reportCard.subjects.map((subject, index) => (
                  <Card key={index}>
                    <CardHeader>
                      <Flex align="center">
                        <HStack>
                          <Icon as={FaBookOpen} color="blue.500" />
                          <Heading size="sm">{subject.subject_name}</Heading>
                        </HStack>
                        <Spacer />
                        <Badge
                          colorScheme={
                            subject.overall_score >= 80 ? 'green' :
                            subject.overall_score >= 60 ? 'yellow' : 'red'
                          }
                          fontSize="md"
                          px={3}
                          py={1}
                        >
                          {subject.grade || 'N/A'}
                        </Badge>
                      </Flex>
                    </CardHeader>
                    <CardBody>
                      <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
                        <VStack align="start" spacing={2}>
                          <Text fontSize="sm" color="gray.600">CA Score (40%)</Text>
                          <Text fontSize="lg" fontWeight="bold">
                            {subject.ca_score} / 100
                          </Text>
                        </VStack>
                        
                        <VStack align="start" spacing={2}>
                          <Text fontSize="sm" color="gray.600">Exam Score (60%)</Text>
                          <Text fontSize="lg" fontWeight="bold">
                            {subject.exam_score} / 100
                          </Text>
                        </VStack>
                        
                        <VStack align="start" spacing={2}>
                          <Text fontSize="sm" color="gray.600">Overall Score</Text>
                          <Text fontSize="lg" fontWeight="bold">
                            {subject.overall_score} / 100
                          </Text>
                          <Progress 
                            value={subject.overall_score} 
                            colorScheme={
                              subject.overall_score >= 80 ? 'green' :
                              subject.overall_score >= 60 ? 'yellow' : 'red'
                            }
                            w="full"
                          />
                          <Text fontSize="sm" color="gray.500">
                            {subject.overall_score.toFixed(1)}%
                          </Text>
                        </VStack>
                        
                        <VStack align="start" spacing={2}>
                          <Text fontSize="sm" color="gray.600">Grade Points</Text>
                          <Text fontSize="lg" fontWeight="bold" color="blue.600">
                            {subject.grade_points.toFixed(1)}
                          </Text>
                        </VStack>
                      </Grid>

                      <Divider my={4} />
                      <Box>
                        <Text fontSize="sm" color="gray.600" mb={2}>
                          Academic Year: {reportCard.academic_year} | Term: {reportCard.term}
                        </Text>
                        <Text fontSize="sm" color={subject.is_finalized ? 'green.600' : 'orange.600'}>
                          Status: {subject.is_finalized ? 'Finalized' : 'Pending'}
                        </Text>
                      </Box>
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
                  onClick={() => navigate(`/parent/communications?child=${child.id}`)}
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
                        .sort((a, b) => (b.percentage || 0) - (a.percentage || 0))
                        .map((record, index) => (
                          <HStack key={index} justify="space-between">
                            <Text fontWeight="medium">{record.subject}</Text>
                            <HStack>
                              <Progress 
                                value={record.percentage || 0} 
                                w="100px"
                                colorScheme={
                                  (record.percentage || 0) >= 80 ? 'green' :
                                  (record.percentage || 0) >= 60 ? 'yellow' : 'red'
                                }
                              />
                              <Text fontSize="sm" w="50px" textAlign="right">
                                {(record.percentage || 0).toFixed(1)}%
                              </Text>
                              <Badge colorScheme="blue">{record.grade || 'N/A'}</Badge>
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
                    {currentTermRecords.filter(r => (r.percentage || 0) >= 80).length > 0 && (
                      <ListItem>
                        <ListIcon as={FaCheckCircle} color="green.500" />
                        <Text as="span">
                          Excellent performance in {currentTermRecords.filter(r => (r.percentage || 0) >= 80).length} subject(s)
                        </Text>
                      </ListItem>
                    )}
                    {currentTermRecords.filter(r => (r.percentage || 0) < 60).length > 0 && (
                      <ListItem>
                        <ListIcon as={FaExclamationTriangle} color="orange.500" />
                        <Text as="span">
                          Needs attention in {currentTermRecords.filter(r => (r.percentage || 0) < 60).length} subject(s)
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
