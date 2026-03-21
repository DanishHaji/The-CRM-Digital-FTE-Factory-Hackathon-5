import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';
import { FaUser, FaEnvelope, FaCalendar, FaSpinner, FaEdit, FaSave, FaTimes } from 'react-icons/fa';
import { useAuth } from '../contexts/AuthContext';
import Navigation from '../components/Navigation';

export default function Profile() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState({ type: '', text: '' });
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setEmail(user.email || '');
    }
  }, [user]);

  const handleSave = () => {
    try {
      const updatedUser = {
        ...user,
        name,
        email,
      };

      localStorage.setItem('user', JSON.stringify(updatedUser));
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      setEditing(false);

      // Reload page to reflect changes
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update profile. Please try again.' });
    }
  };

  const handleCancel = () => {
    setName(user?.name || '');
    setEmail(user?.email || '');
    setEditing(false);
    setMessage({ type: '', text: '' });
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <FaSpinner className="text-4xl text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
      <Navigation />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-500 to-blue-600 px-8 py-12 text-white">
            <div className="flex items-center gap-6">
              <motion.div
                whileHover={{ scale: 1.1 }}
                className="w-24 h-24 bg-white rounded-full flex items-center justify-center text-purple-600 text-4xl font-bold shadow-lg"
              >
                {user.name?.charAt(0).toUpperCase() || 'U'}
              </motion.div>
              <div>
                <h1 className="text-3xl font-bold mb-2">{user.name || 'User'}</h1>
                <p className="text-purple-100">{user.email}</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-8">
            {message.text && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`mb-6 p-4 rounded-lg ${
                  message.type === 'success'
                    ? 'bg-green-50 border-l-4 border-green-500 text-green-700'
                    : 'bg-red-50 border-l-4 border-red-500 text-red-700'
                }`}
              >
                {message.text}
              </motion.div>
            )}

            <div className="space-y-6">
              {/* Name Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <FaUser className="inline mr-2" />
                  Full Name
                </label>
                {editing ? (
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="Enter your name"
                  />
                ) : (
                  <div className="px-4 py-3 bg-gray-50 rounded-lg text-gray-800">
                    {user.name || 'Not set'}
                  </div>
                )}
              </div>

              {/* Email Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <FaEnvelope className="inline mr-2" />
                  Email Address
                </label>
                {editing ? (
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="Enter your email"
                  />
                ) : (
                  <div className="px-4 py-3 bg-gray-50 rounded-lg text-gray-800">
                    {user.email}
                  </div>
                )}
              </div>

              {/* Account Created */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <FaCalendar className="inline mr-2" />
                  Account Created
                </label>
                <div className="px-4 py-3 bg-gray-50 rounded-lg text-gray-800">
                  {user.createdAt
                    ? new Date(user.createdAt).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })
                    : 'Unknown'}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-8 flex gap-4">
              {editing ? (
                <>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleSave}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-blue-600 text-white rounded-lg shadow-lg hover:from-purple-600 hover:to-blue-700 transition-all"
                  >
                    <FaSave />
                    Save Changes
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleCancel}
                    className="flex items-center gap-2 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-all"
                  >
                    <FaTimes />
                    Cancel
                  </motion.button>
                </>
              ) : (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setEditing(true)}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-blue-600 text-white rounded-lg shadow-lg hover:from-purple-600 hover:to-blue-700 transition-all"
                >
                  <FaEdit />
                  Edit Profile
                </motion.button>
              )}
            </div>
          </div>
        </motion.div>

        {/* Additional Info Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-8 bg-white rounded-2xl shadow-lg p-8"
        >
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Account Information</h2>
          <div className="space-y-3 text-gray-600">
            <p>
              <strong>User ID:</strong> {user.id}
            </p>
            <p>
              <strong>Account Status:</strong>{' '}
              <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-semibold">
                Active
              </span>
            </p>
            <p>
              <strong>Subscription:</strong> Free Plan
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
