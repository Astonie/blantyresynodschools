import React from 'react'
import { 
  Box, 
  Button, 
  Container, 
  Heading, 
  Text, 
  VStack, 
  HStack, 
  SimpleGrid, 
  Icon, 
  useColorModeValue,
  Image,
  Badge,
  Flex,
  Link,
  Stack,
  IconButton
} from '@chakra-ui/react'
import { 
  FaGraduationCap, 
  FaUsers, 
  FaBook, 
  FaChartLine, 
  FaPhone, 
  FaEnvelope, 
  FaMapMarkerAlt,
  FaFacebook,
  FaTwitter,
  FaInstagram
} from 'react-icons/fa'

const features = [
  {
    icon: FaGraduationCap,
    title: "Academic Excellence",
    description: "Consistently high academic performance with dedicated teachers and modern curriculum"
  },
  {
    icon: FaUsers,
    title: "Character Development",
    description: "Holistic education focusing on moral values, leadership, and community service"
  },
  {
    icon: FaBook,
    title: "Modern Facilities",
    description: "State-of-the-art classrooms, laboratories, and technology integration"
  },
  {
    icon: FaChartLine,
    title: "Future Ready",
    description: "Preparing students for university and career success in the 21st century"
  }
]

const schools = [
  {
    name: "St. Andrews International Primary School",
    location: "Blantyre",
    type: "Primary",
    badge: "Excellence"
  },
  {
    name: "St. Andrews International Secondary School",
    location: "Blantyre",
    type: "Secondary",
    badge: "Leadership"
  },
  {
    name: "St. Andrews International High School",
    location: "Blantyre",
    type: "High School",
    badge: "Innovation"
  }
]

export default function LandingPage() {
  const bgColor = useColorModeValue('gray.50', 'gray.900')
  const cardBg = useColorModeValue('white', 'gray.800')
  const textColor = useColorModeValue('gray.600', 'gray.300')
  const headingColor = useColorModeValue('gray.800', 'white')

  return (
    <Box>
      {/* Hero Section */}
      <Box 
        bg="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        color="white"
        py={20}
        position="relative"
        overflow="hidden"
      >
        <Container maxW="container.xl">
          <VStack spacing={8} textAlign="center">
            {/* Logo Section */}
            <Box 
              w="120px" 
              h="120px" 
              mx="auto" 
              mb={4}
              position="relative"
            >
              <Image
                src="/logo.jpg"
                alt="CCAP Blantyre Synod Logo"
                w="full"
                h="full"
                objectFit="contain"
              />
            </Box>
            
            <Heading size="2xl" fontWeight="bold">
              Welcome to Blantyre Synod Schools
            </Heading>
            <Text fontSize="xl" maxW="2xl">
              Nurturing minds, building character, and shaping futures through excellence in education. 
              Join our community of learners committed to academic achievement and moral development.
            </Text>
            <HStack spacing={4}>
              <Button 
                size="lg" 
                colorScheme="whiteAlpha" 
                variant="outline"
                onClick={() => window.location.href = '/login'}
              >
                Parent Portal
              </Button>
              <Button 
                size="lg" 
                colorScheme="whiteAlpha"
                onClick={() => window.location.href = '/login'}
              >
                Student Login
              </Button>
            </HStack>
          </VStack>
        </Container>
        
        {/* Decorative elements */}
        <Box
          position="absolute"
          top="10%"
          right="10%"
          w="200px"
          h="200px"
          borderRadius="full"
          bg="rgba(255,255,255,0.1)"
          opacity={0.3}
        />
        <Box
          position="absolute"
          bottom="10%"
          left="10%"
          w="150px"
          h="150px"
          borderRadius="full"
          bg="rgba(255,255,255,0.1)"
          opacity={0.3}
        />
      </Box>

      {/* Features Section */}
      <Box py={20} bg={bgColor}>
        <Container maxW="container.xl">
          <VStack spacing={16}>
            <VStack spacing={4} textAlign="center">
              <Heading color={headingColor}>Why Choose Blantyre Synod Schools?</Heading>
              <Text color={textColor} fontSize="lg" maxW="2xl">
                We provide a comprehensive educational experience that goes beyond academics, 
                fostering well-rounded individuals ready to make a positive impact in society.
              </Text>
            </VStack>
            
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={8}>
              {features.map((feature, index) => (
                <Box
                  key={index}
                  bg={cardBg}
                  p={8}
                  borderRadius="xl"
                  textAlign="center"
                  boxShadow="lg"
                  transition="all 0.3s"
                  _hover={{ transform: 'translateY(-5px)', boxShadow: 'xl' }}
                >
                  <Icon as={feature.icon} w={12} h={12} color="blue.500" mb={4} />
                  <Heading size="md" color={headingColor} mb={3}>
                    {feature.title}
                  </Heading>
                  <Text color={textColor}>
                    {feature.description}
                  </Text>
                </Box>
              ))}
            </SimpleGrid>
          </VStack>
        </Container>
      </Box>

      {/* Schools Section */}
      <Box py={20}>
        <Container maxW="container.xl">
          <VStack spacing={16}>
            <VStack spacing={4} textAlign="center">
              <Heading color={headingColor}>Our Schools</Heading>
              <Text color={textColor} fontSize="lg" maxW="2xl">
                Discover our network of exceptional schools, each committed to providing 
                quality education and nurturing the potential of every student.
              </Text>
            </VStack>
            
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={8} w="full">
              {schools.map((school, index) => (
                <Box
                  key={index}
                  bg={cardBg}
                  p={6}
                  borderRadius="xl"
                  boxShadow="lg"
                  transition="all 0.3s"
                  _hover={{ transform: 'translateY(-5px)', boxShadow: 'xl' }}
                >
                  <VStack spacing={4} align="stretch">
                    <Badge colorScheme="blue" alignSelf="flex-start">
                      {school.badge}
                    </Badge>
                    <Heading size="md" color={headingColor}>
                      {school.name}
                    </Heading>
                    <Text color={textColor} fontSize="sm">
                      <Icon as={FaMapMarkerAlt} mr={2} />
                      {school.location}
                    </Text>
                    <Text color="blue.500" fontWeight="semibold">
                      {school.type}
                    </Text>
                  </VStack>
                </Box>
              ))}
            </SimpleGrid>
          </VStack>
        </Container>
      </Box>

      {/* Statistics Section */}
      <Box py={20} bg="linear-gradient(135deg, #667eea 0%, #764ba2 100%)" color="white">
        <Container maxW="container.xl">
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={8} textAlign="center">
            <VStack>
              <Heading size="2xl" fontWeight="bold">500+</Heading>
              <Text>Students</Text>
            </VStack>
            <VStack>
              <Heading size="2xl" fontWeight="bold">50+</Heading>
              <Text>Teachers</Text>
            </VStack>
            <VStack>
              <Heading size="2xl" fontWeight="bold">95%</Heading>
              <Text>Pass Rate</Text>
            </VStack>
            <VStack>
              <Heading size="2xl" fontWeight="bold">25+</Heading>
              <Text>Years</Text>
            </VStack>
          </SimpleGrid>
        </Container>
      </Box>

      {/* Contact Section */}
      <Box py={20} bg={bgColor}>
        <Container maxW="container.xl">
          <VStack spacing={16}>
            <VStack spacing={4} textAlign="center">
              <Heading color={headingColor}>Get in Touch</Heading>
              <Text color={textColor} fontSize="lg" maxW="2xl">
                Ready to join our community? Contact us to learn more about enrollment, 
                programs, and how we can support your child's educational journey.
              </Text>
            </VStack>
            
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={12} w="full">
              <VStack spacing={6} align="stretch">
                <Box>
                  <Heading size="md" color={headingColor} mb={4}>Contact Information</Heading>
                  <VStack spacing={4} align="stretch">
                    <HStack>
                      <Icon as={FaPhone} color="blue.500" />
                      <Text color={textColor}>+265 1 234 567</Text>
                    </HStack>
                    <HStack>
                      <Icon as={FaEnvelope} color="blue.500" />
                      <Text color={textColor}>info@blantyresynodschools.org</Text>
                    </HStack>
                    <HStack>
                      <Icon as={FaMapMarkerAlt} color="blue.500" />
                      <Text color={textColor}>Blantyre, Malawi</Text>
                    </HStack>
                  </VStack>
                </Box>
                
                <Box>
                  <Heading size="md" color={headingColor} mb={4}>Follow Us</Heading>
                  <HStack spacing={4}>
                    <IconButton
                      aria-label="Facebook"
                      icon={<FaFacebook />}
                      colorScheme="blue"
                      variant="outline"
                      size="lg"
                    />
                    <IconButton
                      aria-label="Twitter"
                      icon={<FaTwitter />}
                      colorScheme="blue"
                      variant="outline"
                      size="lg"
                    />
                    <IconButton
                      aria-label="Instagram"
                      icon={<FaInstagram />}
                      colorScheme="blue"
                      variant="outline"
                      size="lg"
                    />
                  </HStack>
                </Box>
              </VStack>
              
              <Box>
                <Heading size="md" color={headingColor} mb={4}>Quick Actions</Heading>
                <VStack spacing={4} align="stretch">
                  <Button 
                    colorScheme="blue" 
                    size="lg" 
                    onClick={() => window.location.href = '/login'}
                  >
                    Access Parent Portal
                  </Button>
                  <Button 
                    variant="outline" 
                    colorScheme="blue" 
                    size="lg"
                    onClick={() => window.location.href = '/login'}
                  >
                    Student Login
                  </Button>
                  <Button 
                    variant="outline" 
                    colorScheme="purple" 
                    size="lg"
                    onClick={() => window.location.href = '/super-admin/login'}
                  >
                    Super Admin Portal
                  </Button>
                  <Button 
                    variant="ghost" 
                    colorScheme="blue" 
                    size="lg"
                  >
                    Download Brochure
                  </Button>
                </VStack>
              </Box>
            </SimpleGrid>
          </VStack>
        </Container>
      </Box>

      {/* Footer */}
      <Box bg="gray.800" color="white" py={12}>
        <Container maxW="container.xl">
          <VStack spacing={8}>
            {/* Footer Logo */}
            <Box 
              w="80px" 
              h="80px" 
              mx="auto" 
              position="relative"
            >
              <Image
                src="/logo.jpg"
                alt="CCAP Blantyre Synod Logo"
                w="full"
                h="full"
                objectFit="contain"
              />
            </Box>
            
            <Text fontSize="lg" fontWeight="semibold">
              Blantyre Synod Schools
            </Text>
            <Text color="gray.400" textAlign="center" maxW="2xl">
              Empowering students with knowledge, character, and faith. 
              Building a brighter future for Malawi through quality education.
            </Text>
            <Text color="gray.500" fontSize="sm">
              © 2025 Blantyre Synod Schools. All rights reserved.
            </Text>
          </VStack>
        </Container>
      </Box>
    </Box>
  )
}
