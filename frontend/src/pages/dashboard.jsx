import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';
import {
  FaTicketAlt,
  FaClock,
  FaCheckCircle,
  FaExclamationCircle,
  FaSpinner,
  FaPlus,
  FaSearch,
} from 'react-icons/fa';
import { useAuth } from '../contexts/AuthContext';
import Navigation from '../components/Navigation';

export default function Dashboard() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (user && typeof window !== 'undefined') {
      // Load tickets from localStorage (in production, fetch from backend API)
      const storedTickets = localStorage.getItem(`tickets_${user.email}`);
      if (storedTickets) {
        try {
          setTickets(JSON.parse(storedTickets));
        } catch (error) {
          console.error('Error loading tickets:', error);
        }
      }
      setLoading(false);
    }
  }, [user]);

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'resolved':
        return <FaCheckCircle className="text-green-500" />;
      case 'in_progress':
      case 'in progress':
        return <FaSpinner className="text-blue-500 animate-spin" />;
      case 'escalated':
        return <FaExclamationCircle className="text-red-500" />;
      default:
        return <FaClock className="text-yellow-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const baseClasses = 'px-3 py-1 rounded-full text-xs font-semibold';
    switch (status?.toLowerCase()) {
      case 'resolved':
        return `${baseClasses} bg-green-100 text-green-700`;
      case 'in_progress':
      case 'in progress':
        return `${baseClasses} bg-blue-100 text-blue-700`;
      case 'escalated':
        return `${baseClasses} bg-red-100 text-red-700`;
      default:
        return `${baseClasses} bg-yellow-100 text-yellow-700`;
    }
  };

  const filteredTickets = tickets.filter(
    (ticket) =>
      ticket.subject?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ticket.ticket_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ticket.message?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const stats = {
    total: tickets.length,
    pending: tickets.filter((t) => t.status === 'pending').length,
    inProgress: tickets.filter((t) => t.status === 'in_progress').length,
    resolved: tickets.filter((t) => t.status === 'resolved').length,
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <FaSpinner className="text-4xl text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <motion.h1
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-bold text-gray-800 mb-2"
          >
            Welcome back, {user.name || 'User'}!
          </motion.h1>
          <p className="text-gray-600">Manage and track your support tickets</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl shadow-lg p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Tickets</p>
                <p className="text-3xl font-bold text-gray-800">{stats.total}</p>
              </div>
              <FaTicketAlt className="text-4xl text-blue-500" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl shadow-lg p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Pending</p>
                <p className="text-3xl font-bold text-yellow-600">{stats.pending}</p>
              </div>
              <FaClock className="text-4xl text-yellow-500" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl shadow-lg p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">In Progress</p>
                <p className="text-3xl font-bold text-blue-600">{stats.inProgress}</p>
              </div>
              <FaSpinner className="text-4xl text-blue-500" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-xl shadow-lg p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Resolved</p>
                <p className="text-3xl font-bold text-green-600">{stats.resolved}</p>
              </div>
              <FaCheckCircle className="text-4xl text-green-500" />
            </div>
          </motion.div>
        </div>

        {/* Actions Bar */}
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mb-6">
          <div className="relative w-full sm:w-96">
            <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search tickets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => router.push('/')}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg shadow-lg hover:from-blue-600 hover:to-purple-700 transition-all"
          >
            <FaPlus />
            <span className="font-semibold">Create New Ticket</span>
          </motion.button>
        </div>

        {/* Tickets List */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="p-6 border-b">
            <h2 className="text-2xl font-bold text-gray-800">Your Tickets</h2>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <FaSpinner className="text-4xl text-blue-500 animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading tickets...</p>
            </div>
          ) : filteredTickets.length === 0 ? (
            <div className="p-12 text-center">
              <FaTicketAlt className="text-6xl text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 text-lg mb-2">No tickets found</p>
              <p className="text-gray-500 text-sm">
                {searchQuery ? 'Try a different search term' : 'Create your first support ticket'}
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {filteredTickets.map((ticket, index) => (
                <motion.div
                  key={ticket.ticket_id || index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-6 hover:bg-gray-50 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="text-2xl mt-1">{getStatusIcon(ticket.status)}</div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-800">
                            {ticket.subject || 'Support Request'}
                          </h3>
                          <span className={getStatusBadge(ticket.status)}>
                            {ticket.status?.replace('_', ' ').toUpperCase() || 'PENDING'}
                          </span>
                        </div>
                        <p className="text-gray-600 mb-2 line-clamp-2">{ticket.message}</p>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>Ticket ID: {ticket.ticket_id || 'N/A'}</span>
                          {ticket.created_at && (
                            <span>
                              Created: {new Date(ticket.created_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
