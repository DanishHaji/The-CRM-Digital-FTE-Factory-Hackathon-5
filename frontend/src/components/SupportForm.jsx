/**
 * Professional Web Support Form Component
 * Multi-language, animated, with beautiful design
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FaPaperPlane,
  FaUser,
  FaEnvelope,
  FaCommentDots,
  FaRocket,
  FaClock,
  FaGlobeAmericas,
  FaCheckCircle,
  FaExclamationTriangle,
  FaSearch,
} from 'react-icons/fa';
import { validateForm, sanitizeInput } from './FormValidation';
import { api, ApiError } from '../services/api';
import { translations } from '../utils/translations';
import LanguageSwitcher from './LanguageSwitcher';
import StatusDisplay from './StatusDisplay';
import { useAuth } from '../contexts/AuthContext';

export default function SupportForm() {
  const { user } = useAuth();
  const [lang, setLang] = useState('en');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: '',
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null);
  const [ticketId, setTicketId] = useState('');
  const [searchTicketId, setSearchTicketId] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [ticketStatus, setTicketStatus] = useState(null);
  const [showStatusChecker, setShowStatusChecker] = useState(false);

  const t = translations[lang];
  const isRTL = ['ur', 'ar'].includes(lang);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: sanitizeInput(value)
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate
    const validation = validateForm(formData, t);
    if (!validation.isValid) {
      setErrors(validation.errors);
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const result = await api.submitSupportForm(formData);

      setSubmitStatus('success');
      setTicketId(result.ticket_id);

      // Save ticket to localStorage if user is logged in
      if (user) {
        const ticketData = {
          ticket_id: result.ticket_id,
          subject: formData.message.substring(0, 50) + (formData.message.length > 50 ? '...' : ''),
          message: formData.message,
          status: 'pending',
          created_at: new Date().toISOString(),
          name: formData.name,
          email: formData.email,
        };

        const existingTickets = localStorage.getItem(`tickets_${user.email}`);
        const tickets = existingTickets ? JSON.parse(existingTickets) : [];
        tickets.unshift(ticketData); // Add to beginning
        localStorage.setItem(`tickets_${user.email}`, JSON.stringify(tickets));
      }

      // Reset form
      setFormData({
        name: '',
        email: '',
        message: '',
      });

      // Auto-hide success message after 5 seconds
      setTimeout(() => {
        setSubmitStatus(null);
      }, 5000);

    } catch (error) {
      console.error('Submit error:', error);
      setSubmitStatus('error');

      setTimeout(() => {
        setSubmitStatus(null);
      }, 5000);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCheckStatus = async (e) => {
    e.preventDefault();

    if (!searchTicketId.trim()) {
      return;
    }

    setIsSearching(true);
    setTicketStatus(null);

    try {
      const result = await api.checkTicketStatus(searchTicketId);
      setTicketStatus(result);
    } catch (error) {
      console.error('Check status error:', error);
      setTicketStatus({ error: true, message: error.message });
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 ${isRTL ? 'rtl' : 'ltr'}`}>
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
          }}
          transition={{ duration: 20, repeat: Infinity }}
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            scale: [1.2, 1, 1.2],
            rotate: [90, 0, 90],
          }}
          transition={{ duration: 15, repeat: Infinity }}
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl"
        />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-12">
        {/* Header with Language Switcher */}
        <div className="flex justify-between items-center mb-12">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-2 bg-clip-text text-transparent bg-gradient-to-r from-white to-purple-200">
              {t.title}
            </h1>
            <p className="text-xl text-purple-200">{t.subtitle}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <LanguageSwitcher currentLang={lang} onLanguageChange={setLang} />
          </motion.div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <FeatureCard
            icon={FaRocket}
            title={t.features.instant}
            description={t.features.instantDesc}
            delay={0.2}
            gradient="from-blue-500 to-cyan-500"
          />
          <FeatureCard
            icon={FaClock}
            title={t.features.support247}
            description={t.features.support247Desc}
            delay={0.4}
            gradient="from-purple-500 to-pink-500"
          />
          <FeatureCard
            icon={FaGlobeAmericas}
            title={t.features.crossChannel}
            description={t.features.crossChannelDesc}
            delay={0.6}
            gradient="from-green-500 to-emerald-500"
          />
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Support Form */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="bg-white/95 backdrop-blur-lg rounded-3xl shadow-2xl p-8 border border-white/20"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl">
                <FaCommentDots className="text-white text-2xl" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-800">{t.form.message}</h2>
                <p className="text-gray-600">{t.description}</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Name Input */}
              <InputField
                icon={FaUser}
                name="name"
                type="text"
                placeholder={t.form.namePlaceholder}
                label={t.form.name}
                value={formData.name}
                onChange={handleInputChange}
                error={errors.name}
                isRTL={isRTL}
              />

              {/* Email Input */}
              <InputField
                icon={FaEnvelope}
                name="email"
                type="email"
                placeholder={t.form.emailPlaceholder}
                label={t.form.email}
                value={formData.email}
                onChange={handleInputChange}
                error={errors.email}
                isRTL={isRTL}
              />

              {/* Message Textarea */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  {t.form.message}
                </label>
                <div className="relative">
                  <textarea
                    name="message"
                    rows={5}
                    placeholder={t.form.messagePlaceholder}
                    value={formData.message}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-3 pr-12 border-2 rounded-xl focus:ring-4 focus:ring-indigo-100 focus:border-indigo-500 transition-all outline-none resize-none ${
                      errors.message
                        ? 'border-red-500 focus:border-red-500 focus:ring-red-100'
                        : 'border-gray-200'
                    } ${isRTL ? 'text-right' : ''}`}
                  />
                  <div className={`absolute top-4 ${isRTL ? 'left-4' : 'right-4'}`}>
                    <FaCommentDots className="text-gray-400" />
                  </div>
                </div>
                {errors.message && (
                  <motion.p
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-2 text-sm text-red-600 flex items-center gap-1"
                  >
                    <FaExclamationTriangle /> {errors.message}
                  </motion.p>
                )}
              </div>

              {/* Submit Button */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={isSubmitting}
                className="w-full py-4 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
              >
                {isSubmitting ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    >
                      <FaRocket className="text-xl" />
                    </motion.div>
                    {t.form.submitting}
                  </>
                ) : (
                  <>
                    <FaPaperPlane className="text-xl" />
                    {t.form.submit}
                  </>
                )}
              </motion.button>
            </form>

            {/* Success/Error Messages */}
            <AnimatePresence>
              {submitStatus && (
                <motion.div
                  initial={{ opacity: 0, y: 20, scale: 0.9 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -20, scale: 0.9 }}
                  className={`mt-6 p-4 rounded-xl flex items-start gap-3 ${
                    submitStatus === 'success'
                      ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200'
                      : 'bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-200'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${
                    submitStatus === 'success' ? 'bg-green-500' : 'bg-red-500'
                  }`}>
                    {submitStatus === 'success' ? (
                      <FaCheckCircle className="text-white text-xl" />
                    ) : (
                      <FaExclamationTriangle className="text-white text-xl" />
                    )}
                  </div>
                  <div className="flex-1">
                    <h4 className={`font-bold ${
                      submitStatus === 'success' ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {submitStatus === 'success' ? t.messages.success : t.messages.error}
                    </h4>
                    <p className={`text-sm mt-1 ${
                      submitStatus === 'success' ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {submitStatus === 'success' ? t.messages.successDetail : t.messages.errorDetail}
                    </p>
                    {ticketId && (
                      <p className="text-sm mt-2 font-mono font-semibold text-indigo-600">
                        {t.status.ticketId}: {ticketId}
                      </p>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Status Checker */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="space-y-6"
          >
            {/* Status Checker Card */}
            <div className="bg-white/95 backdrop-blur-lg rounded-3xl shadow-2xl p-8 border border-white/20">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl">
                  <FaSearch className="text-white text-2xl" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">{t.status.checkStatus}</h2>
                  <p className="text-gray-600">Track your support request</p>
                </div>
              </div>

              <form onSubmit={handleCheckStatus} className="space-y-4">
                <InputField
                  icon={FaSearch}
                  name="searchTicketId"
                  type="text"
                  placeholder={t.status.ticketIdPlaceholder}
                  label={t.status.ticketId}
                  value={searchTicketId}
                  onChange={(e) => setSearchTicketId(e.target.value)}
                  isRTL={isRTL}
                />

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  type="submit"
                  disabled={isSearching}
                  className="w-full py-4 px-6 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
                >
                  {isSearching ? (
                    <>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      >
                        <FaSearch />
                      </motion.div>
                      {t.status.checking}
                    </>
                  ) : (
                    <>
                      <FaSearch />
                      {t.status.check}
                    </>
                  )}
                </motion.button>
              </form>
            </div>

            {/* Status Display */}
            <AnimatePresence>
              {ticketStatus && !ticketStatus.error && (
                <StatusDisplay ticket={ticketStatus} t={t} />
              )}

              {ticketStatus && ticketStatus.error && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="bg-white rounded-2xl shadow-xl p-6 border-2 border-red-200"
                >
                  <div className="flex items-center gap-3 text-red-600">
                    <FaExclamationTriangle className="text-2xl" />
                    <div>
                      <h4 className="font-bold">Ticket not found</h4>
                      <p className="text-sm text-gray-600">{ticketStatus.message}</p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

// Reusable Input Field Component
function InputField({ icon: Icon, name, type, placeholder, label, value, onChange, error, isRTL }) {
  return (
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-2">
        {label}
      </label>
      <div className="relative">
        <input
          type={type}
          name={name}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          className={`w-full px-4 py-3 ${isRTL ? 'pr-12 text-right' : 'pl-12'} border-2 rounded-xl focus:ring-4 focus:ring-indigo-100 focus:border-indigo-500 transition-all outline-none ${
            error
              ? 'border-red-500 focus:border-red-500 focus:ring-red-100'
              : 'border-gray-200'
          }`}
        />
        <div className={`absolute top-1/2 -translate-y-1/2 ${isRTL ? 'right-4' : 'left-4'}`}>
          <Icon className="text-gray-400" />
        </div>
      </div>
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 text-sm text-red-600 flex items-center gap-1"
        >
          <FaExclamationTriangle /> {error}
        </motion.p>
      )}
    </div>
  );
}

// Feature Card Component
function FeatureCard({ icon: Icon, title, description, delay, gradient }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay }}
      whileHover={{ y: -5 }}
      className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 hover:bg-white/20 transition-all"
    >
      <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${gradient} mb-4`}>
        <Icon className="text-white text-2xl" />
      </div>
      <h3 className="text-xl font-bold text-white mb-2">{title}</h3>
      <p className="text-purple-200">{description}</p>
    </motion.div>
  );
}
