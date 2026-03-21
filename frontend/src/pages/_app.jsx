/**
 * Next.js App Component
 * Global configuration and styles
 */

import '../styles/globals.css';
import '../styles/support-form.css';
import { AuthProvider } from '../contexts/AuthContext';

export default function App({ Component, pageProps }) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}
