import { useEffect, useState } from 'react'
import { BrowserRouter, Link, Navigate, NavLink, Route, Routes, useParams } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Gavel, LayoutDashboard, ShieldCheck } from 'lucide-react'

type User = {
  id: number
  email: string
  username: string
  full_name: string
  role: 'buyer' | 'admin'
}

type Motorcycle = {
  id: number
  title: string
  description: string
  manufacturer: string
  model: string
  year: number
  mileage: number
  engine_cc: number
  fuel_type: string
  condition: string
  location: string
  start_price: number
  reserve_price: number | null
  image_urls: string[]
  status: string
  seller_name?: string | null
}

type Bid = {
  id: number
  user_id: number
  user_name: string | null
  amount: number
  created_at: string
}

type Auction = {
  id: number
  motorcycle_id: number
  status: string
  start_time: string
  end_time: string
  current_price: number
  minimum_increment: number
  reserve_met: boolean
  winner_id: number | null
  winner_name: string | null
  motorcycle: Motorcycle
  bids: Bid[]
}

type MotorcycleDraft = {
  title: string
  description: string
  manufacturer: string
  model: string
  year: string
  mileage: string
  engine_cc: string
  fuel_type: string
  condition: string
  location: string
  start_price: string
  reserve_price: string
}

type AdminUser = {
  id: number
  email: string
  username: string
  full_name: string
  role: string
  is_active: boolean
  bid_count: number
  created_at: string
}

type AdminStats = {
  users: number
  motorcycles: number
  auctions: number
  bids: number
}

type AuthState = {
  token: string
  user: User
}

const API_BASE = 'http://localhost:8000'
const queryClient = new QueryClient()

function getAuth(): AuthState | null {
  const raw = localStorage.getItem('bikebid-auth')
  return raw ? (JSON.parse(raw) as AuthState) : null
}

function setAuth(auth: AuthState | null) {
  if (!auth) {
    localStorage.removeItem('bikebid-auth')
    return
  }
  localStorage.setItem('bikebid-auth', JSON.stringify(auth))
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const auth = getAuth()
  const headers = new Headers(options.headers || {})
  headers.set('Content-Type', 'application/json')
  if (auth?.token) {
    headers.set('Authorization', `Bearer ${auth.token}`)
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || 'Request failed')
  }
  return data as T
}

function formatMoney(value: number | null | undefined) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value ?? 0)
}

function useMotorcycles() {
  return useQuery({
    queryKey: ['motorcycles'],
    queryFn: () => apiFetch<Motorcycle[]>('/api/v1/motorcycles'),
  })
}

function useAuctions() {
  return useQuery({
    queryKey: ['auctions'],
    queryFn: () => apiFetch<Auction[]>('/api/v1/auctions'),
  })
}

function useMe() {
  const auth = getAuth()
  return useQuery({
    queryKey: ['me'],
    queryFn: () => (auth ? apiFetch<User>('/api/v1/auth/me') : Promise.resolve(null)),
    enabled: Boolean(auth),
  })
}

function HomePage() {
  const motorcyclesQuery = useMotorcycles()
  const auctionsQuery = useAuctions()
  const featured = motorcyclesQuery.data?.slice(0, 3) ?? []
  const liveAuctions = auctionsQuery.data?.filter((auction) => auction.status === 'LIVE') ?? []

  return (
    <div className="space-y-10">
      <section className="rounded-3xl bg-slate-900 p-8 text-white shadow-2xl">
        <div className="grid gap-8 md:grid-cols-2 md:items-center">
          <div>
            <p className="mb-3 inline-flex items-center rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">
              Auction marketplace
            </p>
            <h1 className="text-4xl font-black md:text-6xl">Buy your next motorcycle with confidence.</h1>
            <p className="mt-4 max-w-xl text-lg text-slate-300">
              Explore used bikes, bid in live auctions, and win the right machine with transparent pricing and secure transactions.
            </p>
            <div className="mt-6 flex gap-4">
              <Link to="/auctions" className="rounded-xl bg-emerald-500 px-5 py-3 font-semibold text-slate-950">View auctions</Link>
              <Link to="/login" className="rounded-xl border border-slate-700 px-5 py-3 font-semibold text-white">Login</Link>
            </div>
          </div>
          <div className="rounded-3xl bg-gradient-to-br from-emerald-500/30 via-slate-800 to-blue-500/10 p-6">
            <div className="rounded-2xl bg-slate-950/60 p-5 shadow-xl">
              <div className="flex items-center justify-between text-sm text-slate-300">
                <span>Live bidding</span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-1 text-emerald-300">LIVE</span>
              </div>
              <h2 className="mt-3 text-3xl font-bold text-white">Kawasaki Ninja 650</h2>
              <div className="mt-5 grid grid-cols-2 gap-3 text-sm text-slate-300">
                <div className="rounded-xl bg-slate-800 p-3"><div className="text-slate-400">Current bid</div><div className="mt-2 font-semibold text-white">₹4,500</div></div>
                <div className="rounded-xl bg-slate-800 p-3"><div className="text-slate-400">Time left</div><div className="mt-2 font-semibold text-white">06h 12m</div></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-slate-900">Featured motorcycles</h2>
          <Link to="/auctions" className="text-sm font-semibold text-emerald-700">Browse all</Link>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          {featured.map((bike) => (
            <Link key={bike.id} to={`/motorcycles/${bike.id}`} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <img src={bike.image_urls[0]} alt={bike.title} className="h-52 w-full object-cover" />
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase tracking-wider text-slate-500">{bike.manufacturer}</span>
                  <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700">{bike.condition}</span>
                </div>
                <h3 className="mt-2 text-xl font-bold text-slate-900">{bike.title}</h3>
                <p className="mt-2 text-sm text-slate-600">{bike.model} • {bike.year} • {bike.mileage.toLocaleString()} km</p>
                <div className="mt-4 flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-500">Starting from</div>
                    <div className="text-lg font-bold text-slate-900">{formatMoney(bike.start_price)}</div>
                  </div>
                  <ArrowRight className="text-emerald-600" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="rounded-3xl bg-slate-100 p-6">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-slate-900">Live auctions</h2>
          <span className="text-sm text-slate-600">{liveAuctions.length} active</span>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {liveAuctions.map((auction) => (
            <Link to={`/auctions/${auction.id}`} key={auction.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700">{auction.status}</span>
                <span className="text-xs text-slate-500">Ends {new Date(auction.end_time).toLocaleString()}</span>
              </div>
              <h3 className="mt-3 text-xl font-bold text-slate-900">{auction.motorcycle.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{auction.motorcycle.location}</p>
              <div className="mt-4 flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Current bid</div>
                  <div className="text-2xl font-bold text-slate-900">{formatMoney(auction.current_price)}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Min next bid</div>
                  <div className="text-lg font-semibold text-emerald-700">{formatMoney(auction.current_price + auction.minimum_increment)}</div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}

function LoginPage() {
  const [email, setEmail] = useState('admin@bikebid.com')
  const [password, setPassword] = useState('Admin123!')
  const [error, setError] = useState('')

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    try {
      const data = await apiFetch<{ token: string; user: User }>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      setAuth({ token: data.token, user: data.user })
      window.location.href = '/dashboard'
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  return (
    <div className="mx-auto max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-lg">
      <h2 className="text-3xl font-bold text-slate-900">Login</h2>
      <p className="mt-2 text-sm text-slate-600">Use the demo admin or create a buyer account.</p>
      <form onSubmit={submit} className="mt-6 space-y-4">
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-slate-700">Email</span>
          <input value={email} onChange={(event) => setEmail(event.target.value)} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-slate-700">Password</span>
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
        </label>
        {error && <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <button type="submit" className="w-full rounded-xl bg-slate-900 px-4 py-3 font-semibold text-white">Sign in</button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-600">New to BikeBid? <Link to="/register" className="font-semibold text-emerald-700">Create a buyer account</Link></p>
    </div>
  )
}

function RegisterPage() {
  const [form, setForm] = useState({ email: '', username: '', full_name: '', password: '' })
  const [error, setError] = useState('')

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    try {
      const data = await apiFetch<{ token: string; user: User }>('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setAuth({ token: data.token, user: data.user })
      window.location.href = '/dashboard'
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    }
  }

  return (
    <div className="mx-auto max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-lg">
      <h2 className="text-3xl font-bold text-slate-900">Create your buyer account</h2>
      <form onSubmit={submit} className="mt-6 space-y-4">
        {([
          ['full_name', 'Full name'],
          ['username', 'Username'],
          ['email', 'Email'],
          ['password', 'Password'],
        ] as const).map(([field, label]) => (
          <label key={field} className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
            <input
              required
              type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'text'}
              minLength={field === 'password' ? 8 : undefined}
              value={form[field]}
              onChange={(event) => setForm({ ...form, [field]: event.target.value })}
              className="w-full rounded-xl border border-slate-300 px-3 py-2"
            />
          </label>
        ))}
        {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <button className="w-full rounded-xl bg-slate-900 px-4 py-3 font-semibold text-white">Create account</button>
      </form>
    </div>
  )
}

function AuctionsPage() {
  const auctionsQuery = useAuctions()
  const auctions = auctionsQuery.data ?? []

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-3xl font-bold text-slate-900">Auction listings</h2>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600">{auctions.length} auctions</span>
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        {auctions.map((auction) => (
          <Link key={auction.id} to={`/auctions/${auction.id}`} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <img src={auction.motorcycle.image_urls[0]} alt={auction.motorcycle.title} className="h-56 w-full object-cover" />
            <div className="p-5">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-emerald-500/15 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700">{auction.status}</span>
                <span className="text-xs text-slate-500">{new Date(auction.end_time).toLocaleDateString()}</span>
              </div>
              <h3 className="mt-3 text-2xl font-bold text-slate-900">{auction.motorcycle.title}</h3>
              <p className="mt-1 text-sm text-slate-600">{auction.motorcycle.model} • {auction.motorcycle.location}</p>
              <div className="mt-4 flex items-center justify-between text-sm text-slate-700">
                <span>Current bid</span>
                <span className="text-xl font-bold text-slate-900">{formatMoney(auction.current_price)}</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

function AuctionDetailPage({ auctionId }: { auctionId: string }) {
  const auth = getAuth()
  const [bidAmount, setBidAmount] = useState<string | null>(null)
  const [status, setStatus] = useState('')
  const [realtimeConnected, setRealtimeConnected] = useState(false)
  const queryClient = useQueryClient()
  const { data: auction, isLoading, error, refetch } = useQuery({
    queryKey: ['auction', auctionId],
    queryFn: () => apiFetch<Auction>(`/api/v1/auctions/${auctionId}`),
  })

  useEffect(() => {
    if (!auth?.token) return

    let stopped = false
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined
    let socket: WebSocket | undefined
    const connect = () => {
      const websocketBase = API_BASE.replace(/^http/, 'ws')
      socket = new WebSocket(`${websocketBase}/ws/auction/${auctionId}?token=${encodeURIComponent(auth.token)}`)
      socket.onopen = () => setRealtimeConnected(true)
      socket.onmessage = (event) => {
        const message = JSON.parse(event.data) as { event?: string; data?: Auction }
        if (message.data) {
          queryClient.setQueryData(['auction', auctionId], message.data)
          void queryClient.invalidateQueries({ queryKey: ['auctions'] })
        }
      }
      socket.onclose = () => {
        setRealtimeConnected(false)
        if (!stopped) reconnectTimer = setTimeout(connect, 1500)
      }
      socket.onerror = () => socket?.close()
    }

    connect()
    return () => {
      stopped = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [auctionId, auth?.token, queryClient])

  if (isLoading) return <div className="text-slate-600">Loading auction...</div>
  if (error || !auction) return <div className="text-red-600">{error instanceof Error ? error.message : 'Auction not found'}</div>

  const currentAuction = auction

  async function submitBid() {
    if (!auth) {
      setStatus('Please log in to place a bid.')
      return
    }
    try {
      await apiFetch(`/api/v1/auctions/${currentAuction.id}/bid`, {
        method: 'POST',
        body: JSON.stringify({ amount: Number(bidAmount ?? Math.max(currentAuction.current_price + currentAuction.minimum_increment, currentAuction.motorcycle.start_price)) }),
      })
      setStatus('Bid accepted successfully!')
      refetch()
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Bid rejected')
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1.3fr_0.7fr]">
      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <img src={currentAuction.motorcycle.image_urls[0]} alt={currentAuction.motorcycle.title} className="h-80 w-full object-cover" />
        <div className="p-6">
          <div className="flex items-center justify-between">
            <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700">{currentAuction.status}</span>
            <span className="text-sm text-slate-500">Ends {new Date(currentAuction.end_time).toLocaleString()}</span>
          </div>
          <h2 className="mt-4 text-3xl font-bold text-slate-900">{currentAuction.motorcycle.title}</h2>
          <p className="mt-3 text-slate-700">{currentAuction.motorcycle.description}</p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl bg-slate-100 p-4"><div className="text-xs uppercase tracking-wide text-slate-500">Manufacturer</div><div className="mt-2 font-semibold">{currentAuction.motorcycle.manufacturer}</div></div>
            <div className="rounded-2xl bg-slate-100 p-4"><div className="text-xs uppercase tracking-wide text-slate-500">Model</div><div className="mt-2 font-semibold">{currentAuction.motorcycle.model}</div></div>
            <div className="rounded-2xl bg-slate-100 p-4"><div className="text-xs uppercase tracking-wide text-slate-500">Mileage</div><div className="mt-2 font-semibold">{currentAuction.motorcycle.mileage.toLocaleString()} km</div></div>
            <div className="rounded-2xl bg-slate-100 p-4"><div className="text-xs uppercase tracking-wide text-slate-500">Location</div><div className="mt-2 font-semibold">{currentAuction.motorcycle.location}</div></div>
          </div>
        </div>
      </div>

      <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-slate-900">Live auction</h3>
          {auth && <span className={`text-xs font-semibold ${realtimeConnected ? 'text-emerald-700' : 'text-slate-500'}`}>{realtimeConnected ? 'Live updates connected' : 'Reconnecting...'}</span>}
        </div>
        <div className="mt-5 rounded-2xl bg-slate-100 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500">Current highest bid</div>
          <div className="mt-2 text-3xl font-black text-slate-900">{formatMoney(currentAuction.current_price)}</div>
        </div>
        <div className="mt-5 rounded-2xl bg-emerald-50 p-4 text-emerald-900">
          <div className="text-xs uppercase tracking-wide text-emerald-700">Minimum next bid</div>
          <div className="mt-2 text-2xl font-bold">{formatMoney(currentAuction.current_price + currentAuction.minimum_increment)}</div>
        </div>
        <div className="mt-6 space-y-3">
          <label className="block text-sm font-medium text-slate-700">Your bid</label>
          <input value={bidAmount ?? String(Math.max(currentAuction.current_price + currentAuction.minimum_increment, currentAuction.motorcycle.start_price))} onChange={(event) => setBidAmount(event.target.value)} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
        </div>
        <button onClick={submitBid} className="mt-5 w-full rounded-xl bg-emerald-500 px-4 py-3 font-semibold text-slate-950">Place bid</button>
        {status && <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">{status}</div>}

        <div className="mt-8">
          <h4 className="text-lg font-bold text-slate-900">Bid history</h4>
          <div className="mt-4 space-y-3">
            {currentAuction.bids.slice(0, 5).map((bid) => (
              <div key={bid.id} className="flex items-center justify-between rounded-xl bg-slate-100 px-3 py-2 text-sm">
                <span>{bid.user_name || 'Anonymous'}</span>
                <span className="font-semibold text-slate-900">{formatMoney(bid.amount)}</span>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  )
}

function DashboardPage() {
  const auth = getAuth()
  const me = useMe()
  const { data: stats, error } = useQuery({
    queryKey: ['dashboard', auth?.user.id],
    queryFn: () => apiFetch<{ active_auctions: Auction[]; won_auctions: Auction[]; recent_bids: unknown[] }>('/api/v1/dashboard'),
    enabled: Boolean(auth),
  })

  if (!auth) {
    return <div className="rounded-2xl bg-amber-50 p-5 text-amber-900">Please log in to access your dashboard.</div>
  }

  return (
    <div className="space-y-8">
      <div className="rounded-3xl bg-slate-900 p-6 text-white">
        <div className="flex items-center gap-3">
          <LayoutDashboard className="text-emerald-400" />
          <h2 className="text-3xl font-bold">Welcome back, {me.data?.full_name || auth.user.full_name}</h2>
        </div>
      </div>
      <div className="grid gap-5 md:grid-cols-3">
        <div className="rounded-2xl bg-white p-5 shadow-sm"><div className="text-sm text-slate-500">Active auctions</div><div className="mt-2 text-3xl font-bold text-slate-900">{stats?.active_auctions?.length || 0}</div></div>
        <div className="rounded-2xl bg-white p-5 shadow-sm"><div className="text-sm text-slate-500">Won auctions</div><div className="mt-2 text-3xl font-bold text-slate-900">{stats?.won_auctions?.length || 0}</div></div>
        <div className="rounded-2xl bg-white p-5 shadow-sm"><div className="text-sm text-slate-500">Recent bids</div><div className="mt-2 text-3xl font-bold text-slate-900">{stats?.recent_bids?.length || 0}</div></div>
      </div>
      {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-red-700">{error.message}</p>}
      <div className="flex flex-wrap gap-3">
        <Link to="/my-bids" className="rounded-xl bg-slate-900 px-4 py-2 font-semibold text-white">View bid history</Link>
        <Link to="/my-auctions" className="rounded-xl border border-slate-300 px-4 py-2 font-semibold text-slate-700">View auctions</Link>
      </div>
    </div>
  )
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const auth = getAuth()
  if (!auth) return <Navigate to="/login" replace />
  if (auth.user.role !== 'admin') {
    return <div role="alert" className="rounded-2xl bg-red-50 p-5 text-red-700">Administrator access is required.</div>
  }
  return children
}

function MyBidsPage() {
  const auth = getAuth()
  const { data: bids, isLoading, error } = useQuery({
    queryKey: ['my-bids'],
    queryFn: () => apiFetch<Array<{ id: number; auction_id: number; auction_title: string; amount: number; created_at: string; is_highest_bidder: boolean; auction_status: string }>>('/api/v1/users/me/bids'),
    enabled: Boolean(auth),
  })
  if (!auth) return <Navigate to="/login" replace />
  if (isLoading) return <p>Loading your bids...</p>
  if (error) return <p role="alert" className="text-red-700">{error.message}</p>
  return (
    <section className="rounded-3xl bg-white p-6 shadow-sm">
      <h2 className="text-3xl font-bold text-slate-900">My bids</h2>
      {!bids?.length && <p className="mt-5 text-slate-600">You have not placed any bids yet.</p>}
      <div className="mt-5 divide-y divide-slate-200">
        {bids?.map((bid) => (
          <Link key={bid.id} to={`/auctions/${bid.auction_id}`} className="flex flex-wrap items-center justify-between gap-3 py-4">
            <div><div className="font-semibold text-slate-900">{bid.auction_title}</div><div className="text-sm text-slate-500">{new Date(bid.created_at).toLocaleString()}</div></div>
            <div className="text-right"><div className="font-bold">{formatMoney(bid.amount)}</div><div className="text-xs text-slate-500">{bid.auction_status === 'ENDED' && bid.is_highest_bidder ? 'Winner' : bid.auction_status}</div></div>
          </Link>
        ))}
      </div>
    </section>
  )
}

function MyAuctionsPage() {
  const auth = getAuth()
  const { data: auctions, isLoading, error } = useQuery({
    queryKey: ['my-auctions'],
    queryFn: () => apiFetch<Auction[]>('/api/v1/users/me/auctions'),
    enabled: Boolean(auth),
  })
  if (!auth) return <Navigate to="/login" replace />
  if (isLoading) return <p>Loading your auctions...</p>
  if (error) return <p role="alert" className="text-red-700">{error.message}</p>
  return (
    <section className="rounded-3xl bg-white p-6 shadow-sm">
      <h2 className="text-3xl font-bold text-slate-900">My auctions</h2>
      {!auctions?.length && <p className="mt-5 text-slate-600">Auctions you bid in will appear here.</p>}
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {auctions?.map((auction) => (
          <Link key={auction.id} to={`/auctions/${auction.id}`} className="rounded-2xl border border-slate-200 p-4">
            <div className="flex justify-between"><strong>{auction.motorcycle.title}</strong><span className="text-sm">{auction.status}</span></div>
            <div className="mt-2 text-slate-600">Current bid {formatMoney(auction.current_price)}</div>
          </Link>
        ))}
      </div>
    </section>
  )
}

const emptyMotorcycle: MotorcycleDraft = {
  title: '',
  description: '',
  manufacturer: '',
  model: '',
  year: String(new Date().getFullYear()),
  mileage: '0',
  engine_cc: '',
  fuel_type: 'Petrol',
  condition: 'Good',
  location: '',
  start_price: '',
  reserve_price: '',
}

function AdminMotorcyclesPage() {
  const auth = getAuth()
  const queryClient = useQueryClient()
  const [form, setForm] = useState(emptyMotorcycle)
  const [imageUrls, setImageUrls] = useState('')
  const [message, setMessage] = useState('')
  const [editing, setEditing] = useState<Motorcycle | null>(null)
  const [editForm, setEditForm] = useState({ title: '', description: '', location: '', start_price: '' })
  const { data: motorcycles, isLoading, error } = useQuery({
    queryKey: ['admin-motorcycles'],
    queryFn: () => apiFetch<Motorcycle[]>('/api/v1/admin/motorcycles?limit=100'),
    enabled: auth?.user.role === 'admin',
  })
  if (!auth) return <Navigate to="/login" replace />

  async function createMotorcycle(event: React.FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      await apiFetch('/api/v1/admin/motorcycles', {
        method: 'POST',
        body: JSON.stringify({
          ...form,
          year: Number(form.year),
          mileage: Number(form.mileage),
          engine_cc: Number(form.engine_cc),
          image_urls: imageUrls.split(',').map((url) => url.trim()).filter(Boolean),
          reserve_price: form.reserve_price || null,
        }),
      })
      setForm(emptyMotorcycle)
      setImageUrls('')
      setMessage('Motorcycle listing created.')
      await queryClient.invalidateQueries({ queryKey: ['admin-motorcycles'] })
      await queryClient.invalidateQueries({ queryKey: ['motorcycles'] })
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not create listing.')
    }
  }

  async function saveMotorcycle(event: React.FormEvent) {
    event.preventDefault()
    if (!editing) return
    try {
      await apiFetch(`/api/v1/admin/motorcycles/${editing.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ ...editForm, start_price: editForm.start_price }),
      })
      setMessage('Motorcycle listing updated.')
      setEditing(null)
      await queryClient.invalidateQueries({ queryKey: ['admin-motorcycles'] })
      await queryClient.invalidateQueries({ queryKey: ['motorcycles'] })
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not update listing.')
    }
  }

  async function archiveMotorcycle(id: number) {
    try {
      await apiFetch(`/api/v1/admin/motorcycles/${id}`, { method: 'DELETE' })
      setMessage('Motorcycle listing archived.')
      await queryClient.invalidateQueries({ queryKey: ['admin-motorcycles'] })
      await queryClient.invalidateQueries({ queryKey: ['motorcycles'] })
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not archive listing.')
    }
  }

  return (
    <RequireAdmin>
      <div className="space-y-6">
        <h2 className="text-3xl font-bold text-slate-900">Motorcycle management</h2>
        <form onSubmit={createMotorcycle} className="grid gap-4 rounded-3xl bg-white p-6 shadow-sm md:grid-cols-2">
          <h3 className="text-xl font-bold md:col-span-2">Add motorcycle</h3>
          {([
            ['title', 'Title'], ['manufacturer', 'Manufacturer'], ['model', 'Model'],
            ['year', 'Year'], ['mileage', 'Mileage (km)'], ['engine_cc', 'Engine (cc)'],
            ['fuel_type', 'Fuel type'], ['condition', 'Condition'], ['location', 'Location'],
            ['start_price', 'Starting price'], ['reserve_price', 'Reserve price (optional)'],
          ] as const).map(([field, label]) => (
            <label key={field} className="text-sm font-medium text-slate-700">
              {label}
              <input
                required={field !== 'reserve_price'}
                type={['year', 'mileage', 'engine_cc'].includes(field) ? 'number' : 'text'}
                min={['year', 'mileage', 'engine_cc'].includes(field) ? 0 : undefined}
                value={form[field]}
                onChange={(event) => setForm({ ...form, [field]: event.target.value })}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2"
              />
            </label>
          ))}
          <label className="text-sm font-medium text-slate-700 md:col-span-2">
            Description
            <textarea required value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} className="mt-1 min-h-24 w-full rounded-xl border border-slate-300 px-3 py-2" />
          </label>
          <label className="text-sm font-medium text-slate-700 md:col-span-2">
            Image URLs (comma-separated)
            <input value={imageUrls} onChange={(event) => setImageUrls(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" />
          </label>
          {message && <p role="status" className="text-sm text-slate-700 md:col-span-2">{message}</p>}
          <button className="rounded-xl bg-slate-900 px-4 py-3 font-semibold text-white md:col-span-2">Create listing</button>
        </form>
        <section className="rounded-3xl bg-white p-6 shadow-sm">
          <h3 className="text-xl font-bold">Listings</h3>
          {isLoading && <p className="mt-3">Loading listings...</p>}
          {error && <p role="alert" className="mt-3 text-red-700">{error.message}</p>}
          {message && <p role="status" className="mt-3 text-sm text-slate-700">{message}</p>}
          <div className="mt-4 divide-y divide-slate-200">
            {motorcycles?.map((bike) => (
              <div key={bike.id} className="py-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div><strong>{bike.title}</strong><div className="text-sm text-slate-500">{bike.year} · {bike.location} · {bike.status}</div></div>
                  <div className="flex items-center gap-3"><span className="font-semibold">{formatMoney(bike.start_price)}</span>
                    <button onClick={() => { setEditing(bike); setEditForm({ title: bike.title, description: bike.description, location: bike.location, start_price: String(bike.start_price) }) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">Edit</button>
                    {bike.status !== 'ARCHIVED' && <button onClick={() => void archiveMotorcycle(bike.id)} className="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-700">Archive</button>}
                  </div>
                </div>
                {editing?.id === bike.id && (
                  <form onSubmit={saveMotorcycle} className="mt-4 grid gap-3 rounded-xl bg-slate-50 p-4 md:grid-cols-2">
                    <input required aria-label="Motorcycle title" value={editForm.title} onChange={(event) => setEditForm({ ...editForm, title: event.target.value })} className="rounded-lg border border-slate-300 px-3 py-2" />
                    <input required aria-label="Location" value={editForm.location} onChange={(event) => setEditForm({ ...editForm, location: event.target.value })} className="rounded-lg border border-slate-300 px-3 py-2" />
                    <input required aria-label="Starting price" type="number" min="0.01" step="0.01" value={editForm.start_price} onChange={(event) => setEditForm({ ...editForm, start_price: event.target.value })} className="rounded-lg border border-slate-300 px-3 py-2" />
                    <textarea required aria-label="Description" value={editForm.description} onChange={(event) => setEditForm({ ...editForm, description: event.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 md:col-span-2" />
                    <div className="flex gap-2 md:col-span-2">
                      <button className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white">Save changes</button>
                      <button type="button" onClick={() => setEditing(null)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">Cancel</button>
                    </div>
                  </form>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </RequireAdmin>
  )
}

function AdminAuctionsPage() {
  const auth = getAuth()
  const queryClient = useQueryClient()
  const [motorcycleId, setMotorcycleId] = useState('')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [increment, setIncrement] = useState('50')
  const [message, setMessage] = useState('')
  const [editingAuction, setEditingAuction] = useState<Auction | null>(null)
  const [editSchedule, setEditSchedule] = useState({ start_time: '', end_time: '', minimum_increment: '' })
  const motorcycles = useQuery({
    queryKey: ['admin-motorcycles'],
    queryFn: () => apiFetch<Motorcycle[]>('/api/v1/admin/motorcycles?limit=100'),
    enabled: auth?.user.role === 'admin',
  })
  const auctions = useQuery({
    queryKey: ['admin-auctions'],
    queryFn: () => apiFetch<Auction[]>('/api/v1/admin/auctions'),
    enabled: auth?.user.role === 'admin',
  })
  if (!auth) return <Navigate to="/login" replace />

  async function createAuction(event: React.FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      await apiFetch('/api/v1/admin/auctions', {
        method: 'POST',
        body: JSON.stringify({
          motorcycle_id: Number(motorcycleId),
          start_time: new Date(startTime).toISOString(),
          end_time: new Date(endTime).toISOString(),
          minimum_increment: increment,
        }),
      })
      setMessage('Auction draft created.')
      await queryClient.invalidateQueries({ queryKey: ['admin-auctions'] })
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not create auction.')
    }
  }

  async function scheduleAuction(id: number) {
    try {
      await apiFetch(`/api/v1/admin/auctions/${id}/schedule`, { method: 'POST' })
      setMessage('Auction scheduled.')
      await queryClient.invalidateQueries({ queryKey: ['admin-auctions'] })
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not schedule auction.')
    }
  }

  async function saveAuctionSchedule(event: React.FormEvent) {
    event.preventDefault()
    if (!editingAuction) return
    try {
      await apiFetch(`/api/v1/admin/auctions/${editingAuction.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          start_time: new Date(editSchedule.start_time).toISOString(),
          end_time: new Date(editSchedule.end_time).toISOString(),
          minimum_increment: editSchedule.minimum_increment,
        }),
      })
      setMessage('Auction schedule updated.')
      setEditingAuction(null)
      await queryClient.invalidateQueries({ queryKey: ['admin-auctions'] })
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not update auction.')
    }
  }

  async function cancelAuction(id: number) {
    try {
      await apiFetch(`/api/v1/admin/auctions/${id}/cancel`, { method: 'POST' })
      setMessage('Auction cancelled.')
      await queryClient.invalidateQueries({ queryKey: ['admin-auctions'] })
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not cancel auction.')
    }
  }

  return (
    <RequireAdmin>
      <div className="space-y-6">
        <h2 className="text-3xl font-bold text-slate-900">Auction management</h2>
        <form onSubmit={createAuction} className="grid gap-4 rounded-3xl bg-white p-6 shadow-sm md:grid-cols-2">
          <h3 className="text-xl font-bold md:col-span-2">Create and schedule an auction</h3>
          <label className="text-sm font-medium text-slate-700">Motorcycle
            <select required value={motorcycleId} onChange={(event) => setMotorcycleId(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2">
              <option value="">Select a listing</option>
              {motorcycles.data?.filter((bike) => bike.status === 'ACTIVE').map((bike) => <option key={bike.id} value={bike.id}>{bike.title}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">Minimum increment
            <input required type="number" min="0.01" step="0.01" value={increment} onChange={(event) => setIncrement(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" />
          </label>
          <label className="text-sm font-medium text-slate-700">Starts
            <input required type="datetime-local" value={startTime} onChange={(event) => setStartTime(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" />
          </label>
          <label className="text-sm font-medium text-slate-700">Ends
            <input required type="datetime-local" value={endTime} onChange={(event) => setEndTime(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" />
          </label>
          {message && <p role="status" className="text-sm text-slate-700 md:col-span-2">{message}</p>}
          <button className="rounded-xl bg-slate-900 px-4 py-3 font-semibold text-white md:col-span-2">Create draft</button>
        </form>
        <section className="rounded-3xl bg-white p-6 shadow-sm">
          <h3 className="text-xl font-bold">Auctions</h3>
          {auctions.isLoading && <p className="mt-3">Loading auctions...</p>}
          {auctions.error && <p role="alert" className="mt-3 text-red-700">{auctions.error.message}</p>}
          <div className="mt-4 divide-y divide-slate-200">
            {auctions.data?.map((auction) => (
              <div key={auction.id} className="py-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div><Link to={`/auctions/${auction.id}`} className="font-semibold text-slate-900">{auction.motorcycle.title}</Link><div className="text-sm text-slate-500">{auction.status} · {auction.bids.length} bids · ends {new Date(auction.end_time).toLocaleString()}</div></div>
                  <div className="flex flex-wrap items-center gap-2"><span className="font-bold">{formatMoney(auction.current_price)}</span>
                    {(auction.status === 'DRAFT' || auction.status === 'SCHEDULED') && <button onClick={() => {
                      setEditingAuction(auction)
                      const toLocalInput = (value: string) => {
                        const date = new Date(value)
                        date.setMinutes(date.getMinutes() - date.getTimezoneOffset())
                        return date.toISOString().slice(0, 16)
                      }
                      setEditSchedule({ start_time: toLocalInput(auction.start_time), end_time: toLocalInput(auction.end_time), minimum_increment: String(auction.minimum_increment) })
                    }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">Edit schedule</button>}
                    {auction.status === 'DRAFT' && <button onClick={() => void scheduleAuction(auction.id)} className="rounded-lg bg-emerald-100 px-3 py-2 text-sm font-semibold text-emerald-800">Schedule</button>}
                    {(auction.status === 'DRAFT' || auction.status === 'SCHEDULED') && <button onClick={() => void cancelAuction(auction.id)} className="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-700">Cancel</button>}
                  </div>
                </div>
                {editingAuction?.id === auction.id && (
                  <form onSubmit={saveAuctionSchedule} className="mt-4 grid gap-3 rounded-xl bg-slate-50 p-4 md:grid-cols-3">
                    <label className="text-sm">Starts<input required type="datetime-local" value={editSchedule.start_time} onChange={(event) => setEditSchedule({ ...editSchedule, start_time: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
                    <label className="text-sm">Ends<input required type="datetime-local" value={editSchedule.end_time} onChange={(event) => setEditSchedule({ ...editSchedule, end_time: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
                    <label className="text-sm">Minimum increment<input required type="number" min="0.01" step="0.01" value={editSchedule.minimum_increment} onChange={(event) => setEditSchedule({ ...editSchedule, minimum_increment: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
                    <div className="flex gap-2 md:col-span-3"><button className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white">Save schedule</button><button type="button" onClick={() => setEditingAuction(null)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">Close</button></div>
                  </form>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </RequireAdmin>
  )
}

function AdminUsersPage() {
  const auth = getAuth()
  const queryClient = useQueryClient()
  const [message, setMessage] = useState('')
  const { data: users, isLoading, error } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => apiFetch<AdminUser[]>('/api/v1/admin/users'),
    enabled: auth?.user.role === 'admin',
  })
  if (!auth) return <Navigate to="/login" replace />

  async function toggleUser(user: AdminUser) {
    try {
      await apiFetch(`/api/v1/admin/users/${user.id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !user.is_active }),
      })
      setMessage('Account status updated.')
      await queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not update account status.')
    }
  }

  return (
    <RequireAdmin>
      <section className="rounded-3xl bg-white p-6 shadow-sm">
        <h2 className="text-3xl font-bold text-slate-900">User management</h2>
        {message && <p role="status" className="mt-3 text-sm text-slate-700">{message}</p>}
        {isLoading && <p className="mt-3">Loading users...</p>}
        {error && <p role="alert" className="mt-3 text-red-700">{error.message}</p>}
        <div className="mt-4 divide-y divide-slate-200">
          {users?.map((user) => (
            <div key={user.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
              <div><strong>{user.full_name}</strong><div className="text-sm text-slate-500">{user.email} · {user.role} · {user.bid_count} bids</div></div>
              <button onClick={() => void toggleUser(user)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">{user.is_active ? 'Suspend' : 'Reactivate'}</button>
            </div>
          ))}
        </div>
      </section>
    </RequireAdmin>
  )
}

function AdminPage() {
  const auth = getAuth()
  const { data: stat, error } = useQuery({
    queryKey: ['admin-summary'],
    queryFn: () => apiFetch<AdminStats>('/api/v1/admin/summary'),
    enabled: auth?.user.role === 'admin',
  })

  if (!auth || auth.user.role !== 'admin') {
    return <div className="rounded-2xl bg-red-50 p-5 text-red-700">Administrator access is required.</div>
  }

  return (
    <div className="space-y-6">
      <div className="rounded-3xl bg-slate-900 p-6 text-white">
        <div className="flex items-center gap-3">
          <ShieldCheck className="text-emerald-400" />
          <h2 className="text-3xl font-bold">Admin dashboard</h2>
        </div>
      </div>
      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-red-700">{error.message}</div>}
      <div className="grid gap-5 md:grid-cols-4">
        <div className="rounded-2xl bg-white p-5 shadow-sm"><div className="text-sm text-slate-500">Users</div><div className="mt-2 text-3xl font-bold text-slate-900">{stat?.users ?? 0}</div></div>
        <div className="rounded-2xl bg-white p-5 shadow-sm"><div className="text-sm text-slate-500">Motorcycles</div><div className="mt-2 text-3xl font-bold text-slate-900">{stat?.motorcycles ?? 0}</div></div>
        <div className="rounded-2xl bg-white p-5 shadow-sm"><div className="text-sm text-slate-500">Auctions</div><div className="mt-2 text-3xl font-bold text-slate-900">{stat?.auctions ?? 0}</div></div>
        <div className="rounded-2xl bg-white p-5 shadow-sm"><div className="text-sm text-slate-500">Bids</div><div className="mt-2 text-3xl font-bold text-slate-900">{stat?.bids ?? 0}</div></div>
      </div>
    </div>
  )
}

function MotorcycleDetailPage({ motorcycleId }: { motorcycleId: string }) {
  const { data: motorcycle, isLoading, error } = useQuery({
    queryKey: ['motorcycle', motorcycleId],
    queryFn: () => apiFetch<Motorcycle>(`/api/v1/motorcycles/${motorcycleId}`),
  })

  if (isLoading) return <div className="text-slate-600">Loading motorcycle...</div>
  if (error || !motorcycle) return <div className="text-red-600">{error instanceof Error ? error.message : 'Motorcycle not found'}</div>

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <img src={motorcycle.image_urls[0]} alt={motorcycle.title} className="h-72 w-full rounded-2xl object-cover" />
      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div>
          <h2 className="text-3xl font-bold text-slate-900">{motorcycle.title}</h2>
          <p className="mt-3 text-slate-700">{motorcycle.description}</p>
        </div>
        <div className="rounded-2xl bg-slate-100 p-5">
          <div className="text-sm text-slate-500">Starting price</div>
          <div className="mt-2 text-3xl font-black text-slate-900">{formatMoney(motorcycle.start_price)}</div>
          {motorcycle.reserve_price && <div className="mt-4 text-sm text-slate-700">Reserve: {formatMoney(motorcycle.reserve_price)}</div>}
          <Link to="/auctions" className="mt-5 inline-block rounded-xl bg-emerald-500 px-4 py-2 font-semibold text-slate-950">Back to auctions</Link>
        </div>
      </div>
    </div>
  )
}

function MotorcycleDetailRoute() {
  const { motorcycleId } = useParams()
  return <MotorcycleDetailPage motorcycleId={motorcycleId || ''} />
}

function AuctionDetailRoute() {
  const { auctionId } = useParams()
  return <AuctionDetailPage auctionId={auctionId || ''} />
}

function AppShell() {
  const auth = getAuth()
  const user = auth?.user

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2 font-black text-xl text-slate-900">
            <Gavel className="text-emerald-600" />
            BikeBid
          </div>
          <nav className="hidden gap-6 md:flex">
            <NavLink to="/" className={({ isActive }) => (isActive ? 'text-slate-900 font-semibold' : 'text-slate-600')}>Home</NavLink>
            <NavLink to="/auctions" className={({ isActive }) => (isActive ? 'text-slate-900 font-semibold' : 'text-slate-600')}>Auctions</NavLink>
            {user && <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'text-slate-900 font-semibold' : 'text-slate-600')}>Dashboard</NavLink>}
            {user?.role === 'buyer' && <NavLink to="/my-bids" className={({ isActive }) => (isActive ? 'text-slate-900 font-semibold' : 'text-slate-600')}>My bids</NavLink>}
            {user?.role === 'buyer' && <NavLink to="/my-auctions" className={({ isActive }) => (isActive ? 'text-slate-900 font-semibold' : 'text-slate-600')}>My auctions</NavLink>}
            {user?.role === 'admin' && (
              <>
                <NavLink to="/admin" end className={({ isActive }) => (isActive ? 'text-slate-900 font-semibold' : 'text-slate-600')}>Admin overview</NavLink>
                <NavLink to="/admin/motorcycles" className={({ isActive }) => (isActive ? 'text-slate-900 font-semibold' : 'text-slate-600')}>Motorcycles</NavLink>
                <NavLink to="/admin/auctions" className={({ isActive }) => (isActive ? 'text-slate-900 font-semibold' : 'text-slate-600')}>Auctions</NavLink>
                <NavLink to="/admin/users" className={({ isActive }) => (isActive ? 'text-slate-900 font-semibold' : 'text-slate-600')}>Users</NavLink>
              </>
            )}
          </nav>
          <div className="flex items-center gap-2">
            {!user ? (
              <>
                <Link to="/login" className="rounded-xl border border-slate-300 px-4 py-2 font-semibold text-slate-700">Login</Link>
                <Link to="/register" className="rounded-xl bg-slate-900 px-4 py-2 font-semibold text-white">Register</Link>
              </>
            ) : (
              <button onClick={() => { setAuth(null); window.location.href = '/' }} className="rounded-xl border border-slate-300 px-4 py-2 font-semibold text-slate-700">Logout</button>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/auctions" element={<AuctionsPage />} />
          <Route path="/motorcycles/:motorcycleId" element={<MotorcycleDetailRoute />} />
          <Route path="/auctions/:auctionId" element={<AuctionDetailRoute />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/admin/motorcycles" element={<AdminMotorcyclesPage />} />
          <Route path="/admin/auctions" element={<AdminAuctionsPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/my-bids" element={<MyBidsPage />} />
          <Route path="/my-auctions" element={<MyAuctionsPage />} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
