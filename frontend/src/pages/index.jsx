/**
 * Main Support Page - Digital FTE Web Support Form
 * Entry point for customer support
 */

import Head from 'next/head';
import SupportForm from '../components/SupportForm';

export default function Home() {
  return (
    <>
      <Head>
        <title>Customer Support - Digital FTE 24/7</title>
        <meta name="description" content="Get instant AI-powered customer support 24/7. Contact us via our web form, email, or WhatsApp." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />

        {/* Open Graph / Social Media */}
        <meta property="og:type" content="website" />
        <meta property="og:title" content="Customer Support - Digital FTE 24/7" />
        <meta property="og:description" content="Get instant AI-powered customer support 24/7" />

        {/* Multi-language support */}
        <meta httpEquiv="Content-Language" content="en, ur, ar, es, fr, zh" />
      </Head>

      <main>
        <SupportForm />
      </main>
    </>
  );
}
