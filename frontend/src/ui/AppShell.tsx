import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
	Box,
	Button,
	Flex,
	HStack,
	Spacer,
	Text,
	Select,
	IconButton,
	Menu,
	MenuButton,
	MenuItem,
	MenuList,
	Avatar,
	useDisclosure,
	Stack,
	VStack,
	Divider,
	Image
} from '@chakra-ui/react'
import { HamburgerIcon, CalendarIcon, AtSignIcon, SettingsIcon, EditIcon, ChatIcon, StarIcon, InfoIcon } from '@chakra-ui/icons'
import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { useRBAC } from '../lib/rbac'

export function AppShell() {
  const navigate = useNavigate()
	const [tenant, setTenant] = useState(localStorage.getItem('tenant') || '')
	const [tenants, setTenants] = useState<Array<{ id: number; name: string; slug: string }>>([])
	const { isOpen, onOpen, onClose } = useDisclosure()
	const { getAccessibleMenuItems, user } = useRBAC()

	useEffect(() => {
		const load = async () => {
			try {
				const res = await api.get('/tenants')
				setTenants(res.data || [])
			} catch {
				setTenants([])
			}
		}
		load()
	}, [])

  const [branding, setBranding] = useState<{ logo_url?: string; primary_color?: string; secondary_color?: string } | null>(null)
  const [enabledModules, setEnabledModules] = useState<string[]>([])

  const onTenantChange = (v: string) => {
		localStorage.setItem('tenant', v)
		setTenant(v)
    navigate(0)
  }

  const logout = () => {
    localStorage.removeItem('token')
    navigate('/login', { replace: true })
  }

  useEffect(() => {
    const loadConfig = async () => {
      if (!tenant) return
      try {
        const res = await api.get(`/tenants/public/config`, { params: { slug: tenant } })
        setBranding(res.data.branding || null)
        setEnabledModules(res.data.enabled_modules || [])
      } catch {
        setBranding(null)
        setEnabledModules([])
      }
    }
    loadConfig()
  }, [tenant])

  const show = (mod: string) => enabledModules.length === 0 || enabledModules.includes(mod)

  const primary = branding?.primary_color || undefined
  const headerStyle = primary ? { color: primary } as React.CSSProperties : undefined

	// Icon mapping helper
	const getIcon = (iconName: string) => {
		switch (iconName) {
			case 'StarIcon': return <StarIcon />
			case 'EditIcon': return <EditIcon />
			case 'CalendarIcon': return <CalendarIcon />
			case 'AtSignIcon': return <AtSignIcon />
			case 'ChatIcon': return <ChatIcon />
			case 'InfoIcon': return <InfoIcon />
			case 'SettingsIcon': return <SettingsIcon />
			default: return <StarIcon />
		}
	}

  return (
    <Flex minH="100vh" bg="gray.50">
			{/* Sidebar */}
      <Box as="aside" display={{ base: 'none', md: 'block' }} w="260px" bg="white" borderRightWidth="1px" position="sticky" top={0} h="100vh">
        <Flex p={4} align="center" justify="space-between" borderBottomWidth="1px" position="sticky" top={0} bg="white" zIndex={1}>
					<HStack spacing={3}>
						{/* Small Logo */}
						<Box 
							w="32px" 
							h="32px" 
							position="relative"
						>
							<Image
								src={branding?.logo_url || '/logo.jpg'}
								alt="CCAP Blantyre Synod Logo"
								w="full"
								h="full"
								objectFit="contain"
							/>
						</Box>
						<Text fontWeight="bold" style={headerStyle}>Blantyre Synod</Text>
					</HStack>
				</Flex>
				<VStack align="stretch" spacing={1} p={3}>
					{getAccessibleMenuItems().map((item) => (
						<NavItem key={item.key} to={item.path} icon={getIcon(item.icon)}>
							{item.label}
						</NavItem>
					))}
				</VStack>
			</Box>

      {/* Content area */}
			<Flex direction="column" flex="1">
        <Flex as="header" p={3} bg="white" borderBottomWidth="1px" align="center" gap={4} position="sticky" top={0} zIndex={2}>
					<IconButton aria-label="Open menu" icon={<HamburgerIcon />} variant="ghost" display={{ base: 'inline-flex', md: 'none' }} onClick={onOpen} />
					<Spacer />
					<Select width={{ base: '140px', md: '220px' }} value={tenant} onChange={(e) => onTenantChange(e.target.value)} placeholder="Select tenant">
						{tenants.map((t) => (
							<option key={t.id} value={t.slug}>{t.name}</option>
						))}
					</Select>
					<Menu>
						<MenuButton as={Button} rightIcon={<Avatar size="xs" ml={2} name={user?.full_name || user?.email || tenant} />}>
							{user?.full_name || user?.email || 'Account'}
						</MenuButton>
						<MenuList>
							<MenuItem onClick={() => navigate('/')}>Home</MenuItem>
							{user && (
								<MenuItem isDisabled>
									Role: {user.roles?.join(', ') || 'No roles'}
								</MenuItem>
							)}
							<MenuItem onClick={logout}>Logout</MenuItem>
						</MenuList>
					</Menu>
				</Flex>
				<Box p={6}>
					<Outlet />
				</Box>
			</Flex>

			{/* Mobile drawer menu */}
			{isOpen && (
				<Box position="fixed" inset={0} bg="blackAlpha.600" zIndex={10} onClick={onClose}>
					<Box bg="white" w="260px" h="100%" p={4} onClick={(e) => e.stopPropagation()}>
						<Text fontWeight="bold" mb={3} color="brand.600">Menu</Text>
						<VStack align="stretch" spacing={2}>
							{getAccessibleMenuItems().map((item) => (
								<NavItem key={item.key} to={item.path} onNavigate={onClose} icon={getIcon(item.icon)}>
									{item.label}
								</NavItem>
							))}
							<Divider />
							<Button onClick={() => { onClose(); logout(); }} variant="ghost" justifyContent="flex-start">Logout</Button>
						</VStack>
					</Box>
				</Box>
			)}
		</Flex>
	)
}

type NavItemProps = {
	to: string
	children: React.ReactNode
	icon?: React.ReactNode
	onNavigate?: () => void
}

function NavItem({ to, children, icon, onNavigate }: NavItemProps) {
	return (
		<NavLink
			to={to}
			style={({ isActive }) => ({
				background: isActive ? 'var(--chakra-colors-gray-100)' : 'transparent',
				borderRadius: 8,
				padding: '8px 10px',
				display: 'flex',
				alignItems: 'center',
				gap: 10,
				fontWeight: 500,
			})}
			onClick={onNavigate}
		>
			{icon}
			<span>{children}</span>
		</NavLink>
	)
}



