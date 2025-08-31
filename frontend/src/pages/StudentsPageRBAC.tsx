import React from 'react'
import { 
  Box, 
  Button, 
  Text, 
  VStack, 
  HStack, 
  Alert, 
  AlertIcon, 
  Badge,
  Divider,
  Grid,
  GridItem 
} from '@chakra-ui/react'
import { useRBAC, RBACWrapper, RBACButton } from '../lib/rbac'

export default function StudentsPage() {
  const { user, canPerformAction, getRoleLevel } = useRBAC()

  const roleLevel = getRoleLevel()
  const canCreate = canPerformAction('students', 'create')
  const canUpdate = canPerformAction('students', 'update')
  const canDelete = canPerformAction('students', 'delete')

  return (
    <Box>
      <VStack align="stretch" spacing={6}>
        <Box>
          <HStack justify="space-between" align="center" mb={4}>
            <Text fontSize="2xl" fontWeight="bold">Students Management</Text>
            <HStack>
              <Badge colorScheme="blue">Role Level: {roleLevel}</Badge>
              <Badge colorScheme="green">
                {user?.roles?.join(', ') || 'No roles'}
              </Badge>
            </HStack>
          </HStack>

          {/* Permission-based Action Buttons */}
          <HStack spacing={3}>
            <RBACButton 
              permissions={['students.create']} 
              colorScheme="green"
              onClick={() => console.log('Create student')}
            >
              Create Student
            </RBACButton>

            <RBACButton 
              permissions={['students.update']} 
              colorScheme="blue"
              onClick={() => console.log('Edit student')}
            >
              Edit Students
            </RBACButton>

            <RBACButton 
              permissions={['students.delete']} 
              colorScheme="red"
              onClick={() => console.log('Delete student')}
            >
              Delete Students
            </RBACButton>
          </HStack>
        </Box>

        <Divider />

        {/* Role-specific Sections */}
        <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={6}>
          
          {/* Administrator Section */}
          <RBACWrapper roles={['Administrator', 'Super Administrator']}>
            <GridItem>
              <Box border="1px" borderColor="red.200" borderRadius="md" p={4}>
                <Text fontSize="lg" fontWeight="bold" color="red.600" mb={3}>
                  Administrator Functions
                </Text>
                <VStack align="stretch" spacing={2}>
                  <Button size="sm" colorScheme="red" variant="outline">
                    Bulk Import Students
                  </Button>
                  <Button size="sm" colorScheme="red" variant="outline">
                    System Reports
                  </Button>
                  <Button size="sm" colorScheme="red" variant="outline">
                    Data Export
                  </Button>
                </VStack>
              </Box>
            </GridItem>
          </RBACWrapper>

          {/* School Administrator Section */}
          <RBACWrapper roles={['School Administrator']}>
            <GridItem>
              <Box border="1px" borderColor="blue.200" borderRadius="md" p={4}>
                <Text fontSize="lg" fontWeight="bold" color="blue.600" mb={3}>
                  School Management
                </Text>
                <VStack align="stretch" spacing={2}>
                  <Button size="sm" colorScheme="blue" variant="outline">
                    Class Assignments
                  </Button>
                  <Button size="sm" colorScheme="blue" variant="outline">
                    Academic Records
                  </Button>
                  <Button size="sm" colorScheme="blue" variant="outline">
                    School Reports
                  </Button>
                </VStack>
              </Box>
            </GridItem>
          </RBACWrapper>

          {/* Teacher Section */}
          <RBACWrapper roles={['Teacher']}>
            <GridItem>
              <Box border="1px" borderColor="green.200" borderRadius="md" p={4}>
                <Text fontSize="lg" fontWeight="bold" color="green.600" mb={3}>
                  Teacher Functions
                </Text>
                <VStack align="stretch" spacing={2}>
                  <Button size="sm" colorScheme="green" variant="outline">
                    My Classes
                  </Button>
                  <Button size="sm" colorScheme="green" variant="outline">
                    Grade Students
                  </Button>
                  <Button size="sm" colorScheme="green" variant="outline">
                    Attendance
                  </Button>
                </VStack>
              </Box>
            </GridItem>
          </RBACWrapper>

          {/* Finance Officer Section */}
          <RBACWrapper roles={['Finance Officer']}>
            <GridItem>
              <Box border="1px" borderColor="yellow.200" borderRadius="md" p={4}>
                <Text fontSize="lg" fontWeight="bold" color="yellow.600" mb={3}>
                  Finance Functions
                </Text>
                <VStack align="stretch" spacing={2}>
                  <Button size="sm" colorScheme="yellow" variant="outline">
                    Fee Records
                  </Button>
                  <Button size="sm" colorScheme="yellow" variant="outline">
                    Payment Status
                  </Button>
                  <Button size="sm" colorScheme="yellow" variant="outline">
                    Financial Reports
                  </Button>
                </VStack>
              </Box>
            </GridItem>
          </RBACWrapper>

          {/* Parent Section */}
          <RBACWrapper roles={['Parent']}>
            <GridItem>
              <Box border="1px" borderColor="purple.200" borderRadius="md" p={4}>
                <Text fontSize="lg" fontWeight="bold" color="purple.600" mb={3}>
                  Parent View
                </Text>
                <VStack align="stretch" spacing={2}>
                  <Button size="sm" colorScheme="purple" variant="outline">
                    My Children
                  </Button>
                  <Button size="sm" colorScheme="purple" variant="outline">
                    Report Cards
                  </Button>
                  <Button size="sm" colorScheme="purple" variant="outline">
                    Fee Status
                  </Button>
                </VStack>
              </Box>
            </GridItem>
          </RBACWrapper>
        </Grid>

        {/* Permission Summary */}
        <Box bg="gray.50" p={4} borderRadius="md">
          <Text fontSize="md" fontWeight="bold" mb={3}>Your Access Summary:</Text>
          <Grid templateColumns="repeat(4, 1fr)" gap={4}>
            <Box>
              <Text fontSize="sm" color="gray.600">Create</Text>
              <Text fontSize="lg" color={canCreate ? 'green.500' : 'red.500'}>
                {canCreate ? '✅ Yes' : '❌ No'}
              </Text>
            </Box>
            <Box>
              <Text fontSize="sm" color="gray.600">Read</Text>
              <Text fontSize="lg" color="green.500">✅ Yes</Text>
            </Box>
            <Box>
              <Text fontSize="sm" color="gray.600">Update</Text>
              <Text fontSize="lg" color={canUpdate ? 'green.500' : 'red.500'}>
                {canUpdate ? '✅ Yes' : '❌ No'}
              </Text>
            </Box>
            <Box>
              <Text fontSize="sm" color="gray.600">Delete</Text>
              <Text fontSize="lg" color={canDelete ? 'green.500' : 'red.500'}>
                {canDelete ? '✅ Yes' : '❌ No'}
              </Text>
            </Box>
          </Grid>
        </Box>

        {/* Insufficient Access Warning */}
        <RBACWrapper 
          permissions={[]} 
          fallback={
            <Alert status="warning">
              <AlertIcon />
              You don't have sufficient permissions to view student data. 
              Contact your administrator for access.
            </Alert>
          }
        >
          <Alert status="success">
            <AlertIcon />
            You have full access to the Students module with your current role.
          </Alert>
        </RBACWrapper>

      </VStack>
    </Box>
  )
}
