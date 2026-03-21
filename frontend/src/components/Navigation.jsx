import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FaHome,
  FaTicketAlt,
  FaUser,
  FaSignInAlt,
  FaSignOutAlt,
  FaUserPlus,
  FaBars,
  FaTimes,
} from 'react-icons/fa';
import { useAuth } from '../contexts/AuthContext';

export default function Navigation() {
  const { user, logout, isAuthenticated } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const router = useRouter();

  const handleLogout = () => {
    logout();
    setMobileMenuOpen(false);
  };

  const navigationItems = [
    { name: 'Home', href: '/', icon: FaHome, public: true },
    { name: 'Dashboard', href: '/dashboard', icon: FaTicketAlt, protected: true },
    { name: 'Profile', href: '/profile', icon: FaUser, protected: true },
  ];

  const authItems = isAuthenticated
    ? [{ name: 'Logout', onClick: handleLogout, icon: FaSignOutAlt }]
    : [
        { name: 'Login', href: '/login', icon: FaSignInAlt },
        { name: 'Sign Up', href: '/signup', icon: FaUserPlus },
      ];

  const NavLink = ({ item }) => {
    const isActive = router.pathname === item.href;
    const Icon = item.icon;

    const handleClick = (e) => {
      if (item.onClick) {
        e.preventDefault();
        item.onClick();
      }
      setMobileMenuOpen(false);
    };

    return (
      <Link
        href={item.href || '#'}
        onClick={handleClick}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
          isActive
            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
            : 'text-gray-700 hover:bg-gray-100'
        }`}
      >
        <Icon />
        <span className="font-medium">{item.name}</span>
      </Link>
    );
  };

  return (
    <nav className="bg-white shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.5 }}
              className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center"
            >
              <FaTicketAlt className="text-white text-xl" />
            </motion.div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              Digital FTE
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-4">
            {navigationItems.map((item) => {
              if (item.protected && !isAuthenticated) return null;
              if (item.public === false && !isAuthenticated) return null;
              return <NavLink key={item.name} item={item} />;
            })}

            <div className="ml-4 border-l pl-4 flex items-center gap-4">
              {authItems.map((item) => (
                <NavLink key={item.name} item={item} />
              ))}
            </div>

            {isAuthenticated && user && (
              <div className="ml-2 flex items-center gap-2 text-sm text-gray-600">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
                  {user.name?.charAt(0).toUpperCase() || 'U'}
                </div>
                <span className="font-medium">{user.name || user.email}</span>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {mobileMenuOpen ? <FaTimes size={24} /> : <FaBars size={24} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="md:hidden border-t py-4"
            >
              {isAuthenticated && user && (
                <div className="flex items-center gap-3 px-4 py-3 mb-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
                    {user.name?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-800">{user.name || 'User'}</div>
                    <div className="text-sm text-gray-600">{user.email}</div>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                {navigationItems.map((item) => {
                  if (item.protected && !isAuthenticated) return null;
                  if (item.public === false && !isAuthenticated) return null;
                  return <NavLink key={item.name} item={item} />;
                })}

                <div className="border-t pt-2 mt-2 space-y-2">
                  {authItems.map((item) => (
                    <NavLink key={item.name} item={item} />
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </nav>
  );
}
