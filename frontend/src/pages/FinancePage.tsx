import { useEffect, useState } from 'react'
import { Box, Button, Heading, HStack, Input, SimpleGrid, Text, useToast } from '@chakra-ui/react'
import { api } from '../lib/api'

type Invoice = { id: number; student_id: number; term: string; currency: string; amount: number; status: string }
type Payment = { id: number; invoice_id: number; amount: number; method: string; reference?: string | null }

export default function FinancePage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [form, setForm] = useState({ student_id: '', term: '', amount: '' })
  const toast = useToast()

  const load = async () => {
    const i = await api.get<Invoice[]>('/finance/invoices').catch(() => ({ data: [] }))
    const p = await api.get<Payment[]>('/finance/payments').catch(() => ({ data: [] }))
    setInvoices(i.data)
    setPayments(p.data)
  }

  useEffect(() => {
    load()
  }, [])

  const create = async () => {
    try {
      await api.post('/finance/invoices', { student_id: Number(form.student_id), term: form.term, amount: Number(form.amount) })
      setForm({ student_id: '', term: '', amount: '' })
      await load()
      toast({ title: 'Invoice created', status: 'success' })
    } catch (e: any) {
      toast({ title: 'Error', description: e?.response?.data?.detail || String(e), status: 'error' })
    }
  }

  return (
    <Box>
      <Heading size="md" mb={4}>Finance</Heading>
      <HStack spacing={2} mb={4}>
        <Input placeholder="Student ID" value={form.student_id} onChange={(e) => setForm({ ...form, student_id: e.target.value })} />
        <Input placeholder="Term" value={form.term} onChange={(e) => setForm({ ...form, term: e.target.value })} />
        <Input placeholder="Amount" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
        <Button colorScheme="blue" onClick={create}>Create Invoice</Button>
      </HStack>
      <Heading size="sm" mt={6} mb={2}>Invoices</Heading>
      <SimpleGrid columns={[1, 2, 3]} spacing={3}>
        {invoices.map(i => (
          <Box key={i.id} borderWidth="1px" rounded="md" p={3}>
            <Text fontWeight="bold">Invoice #{i.id}</Text>
            <Text>Student: {i.student_id}</Text>
            <Text>Term: {i.term}</Text>
            <Text>Amount: {i.currency} {i.amount}</Text>
            <Text>Status: {i.status}</Text>
          </Box>
        ))}
      </SimpleGrid>
      <Heading size="sm" mt={6} mb={2}>Payments</Heading>
      <SimpleGrid columns={[1, 2, 3]} spacing={3}>
        {payments.map(p => (
          <Box key={p.id} borderWidth="1px" rounded="md" p={3}>
            <Text fontWeight="bold">Payment #{p.id}</Text>
            <Text>Invoice: {p.invoice_id}</Text>
            <Text>Amount: {p.amount}</Text>
            <Text>Method: {p.method}</Text>
            <Text>Ref: {p.reference || '-'}</Text>
          </Box>
        ))}
      </SimpleGrid>
    </Box>
  )
}



