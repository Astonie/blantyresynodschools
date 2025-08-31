import { useEffect, useState } from 'react'
import { SimpleGrid, Stat, StatLabel, StatNumber, Heading, Box } from '@chakra-ui/react'
import { useMemo } from 'react'
import { Navigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<{ students: number; invoices: number; payments: number }>({ students: 0, invoices: 0, payments: 0 })

  // Redirect parents to their dedicated portal
  const isParent = user?.roles?.includes('Parent') || user?.roles?.includes('Parent (Restricted)')
  if (isParent) {
    return <Navigate to="/parent" replace />
  }

  useEffect(() => {
    const load = async () => {
      try {
        const s = await api.get('/students')
        const i = await api.get('/finance/invoices').catch(() => ({ data: [] }))
        const p = await api.get('/finance/payments').catch(() => ({ data: [] }))
        setStats({ students: s.data.length, invoices: i.data.length, payments: p.data.length })
      } catch {}
    }
    load()
  }, [])

  return (
    <>
      <Heading size="md" mb={4}>Overview</Heading>
      <SimpleGrid columns={[1, 3]} spacing={4}>
        <Stat>
          <StatLabel>Students</StatLabel>
          <StatNumber>{stats.students}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Invoices</StatLabel>
          <StatNumber>{stats.invoices}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Payments</StatLabel>
          <StatNumber>{stats.payments}</StatNumber>
        </Stat>
      </SimpleGrid>
      {/* Placeholder area for future charts (e.g., students by class, fees status) */}
      <Box mt={6} bg="white" borderWidth="1px" rounded="md" p={4}>
        <Heading size="sm" mb={2}>Insights</Heading>
        <Box color="gray.500">Charts coming soon (students by class, fees status, payments trend).</Box>
      </Box>
    </>
  )
}