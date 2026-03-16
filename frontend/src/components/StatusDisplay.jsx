/**
 * Status Display Component
 * Animated ticket status display with timeline
 */

import { motion } from 'framer-motion';
import { FaClock, FaSpinner, FaCheckCircle, FaUserTie } from 'react-icons/fa';

const statusIcons = {
  pending: FaClock,
  processing: FaSpinner,
  responded: FaCheckCircle,
  escalated: FaUserTie,
};

const statusColors = {
  pending: 'from-yellow-400 to-orange-500',
  processing: 'from-blue-400 to-indigo-500',
  responded: 'from-green-400 to-emerald-500',
  escalated: 'from-purple-400 to-pink-500',
};

const statusBgColors = {
  pending: 'bg-yellow-50',
  processing: 'bg-blue-50',
  responded: 'bg-green-50',
  escalated: 'bg-purple-50',
};

export default function StatusDisplay({ ticket, t }) {
  const StatusIcon = statusIcons[ticket.status] || FaClock;
  const statusColor = statusColors[ticket.status] || statusColors.pending;
  const statusBg = statusBgColors[ticket.status] || statusBgColors.pending;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white rounded-2xl shadow-xl p-6 border border-gray-200"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-800">
            {t.status.checkStatus}
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            {t.status.ticketId}: <span className="font-mono font-semibold text-indigo-600">{ticket.ticket_id}</span>
          </p>
        </div>

        <motion.div
          animate={{
            rotate: ticket.status === 'processing' ? 360 : 0,
          }}
          transition={{
            duration: 2,
            repeat: ticket.status === 'processing' ? Infinity : 0,
            ease: 'linear',
          }}
          className={`p-4 rounded-full bg-gradient-to-br ${statusColor}`}
        >
          <StatusIcon className="text-white text-2xl" />
        </motion.div>
      </div>

      {/* Status Badge */}
      <motion.div
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${statusBg} border border-gray-200 mb-6`}
      >
        <div className={`w-2 h-2 rounded-full bg-gradient-to-br ${statusColor}`} />
        <span className="font-semibold text-gray-700">
          {t.statuses[ticket.status]}
        </span>
      </motion.div>

      {/* Timeline */}
      <div className="space-y-4">
        <TimelineItem
          label={t.statuses.pending}
          completed={true}
          active={ticket.status === 'pending'}
          color={statusColors.pending}
        />
        <TimelineItem
          label={t.statuses.processing}
          completed={['processing', 'responded', 'escalated'].includes(ticket.status)}
          active={ticket.status === 'processing'}
          color={statusColors.processing}
        />
        {ticket.status === 'escalated' ? (
          <TimelineItem
            label={t.statuses.escalated}
            completed={ticket.status === 'escalated'}
            active={ticket.status === 'escalated'}
            color={statusColors.escalated}
          />
        ) : (
          <TimelineItem
            label={t.statuses.responded}
            completed={ticket.status === 'responded'}
            active={ticket.status === 'responded'}
            color={statusColors.responded}
          />
        )}
      </div>

      {/* Response (if available) */}
      {ticket.response && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-200"
        >
          <h4 className="font-semibold text-green-800 mb-2 flex items-center gap-2">
            <FaCheckCircle /> Response
          </h4>
          <p className="text-gray-700 whitespace-pre-wrap">
            {ticket.response}
          </p>
        </motion.div>
      )}

      {/* Timestamps */}
      <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-500">Created</p>
          <p className="font-semibold text-gray-700">
            {new Date(ticket.created_at).toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-gray-500">Updated</p>
          <p className="font-semibold text-gray-700">
            {new Date(ticket.updated_at).toLocaleString()}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function TimelineItem({ label, completed, active, color }) {
  return (
    <div className="flex items-center gap-4">
      <motion.div
        animate={{
          scale: active ? [1, 1.2, 1] : 1,
        }}
        transition={{
          duration: 1,
          repeat: active ? Infinity : 0,
        }}
        className="relative"
      >
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
            completed
              ? `bg-gradient-to-br ${color} border-transparent`
              : 'bg-white border-gray-300'
          }`}
        >
          {completed && <FaCheckCircle className="text-white" />}
        </div>
        {active && (
          <motion.div
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
            className={`absolute inset-0 rounded-full bg-gradient-to-br ${color} opacity-50`}
          />
        )}
      </motion.div>

      <div className="flex-1">
        <p className={`font-medium ${completed ? 'text-gray-800' : 'text-gray-400'}`}>
          {label}
        </p>
      </div>
    </div>
  );
}
