# Digital FTE Web Support Form ✨

**Professional, Animated, Multi-Language Customer Support Interface**

A stunning React/Next.js web application providing 24/7 customer support with AI-powered responses. Features beautiful animations, multi-language support, and seamless integration with the Digital FTE backend.

## 🌟 Features

### 🎨 Design & UI
- ✅ **Professional Gradient Design** - Beautiful purple/indigo/pink gradients
- ✅ **Smooth Animations** - Framer Motion animations throughout
- ✅ **Glassmorphism Effects** - Modern frosted glass UI elements
- ✅ **Responsive Design** - Perfect on mobile, tablet, and desktop
- ✅ **Eye-Catching Colors** - Carefully selected color palette
- ✅ **Icon Integration** - React Icons for visual appeal

### 🌍 Multi-Language Support
- 🇬🇧 English
- 🇵🇰 Urdu (اردو) - RTL support
- 🇸🇦 Arabic (العربية) - RTL support
- 🇪🇸 Spanish (Español)
- 🇫🇷 French (Français)
- 🇨🇳 Chinese (中文)

### ⚡ Functionality
- ✅ **Real-Time Form Validation** - Client-side validation with instant feedback
- ✅ **Ticket Status Checking** - Track support requests in real-time
- ✅ **Loading States** - Beautiful loading animations
- ✅ **Success/Error Alerts** - Animated notifications
- ✅ **API Integration** - Backend connectivity for ticket submission
- ✅ **Cross-Channel Support** - Email, WhatsApp, Web form

### 🎭 Animations
- ✅ Smooth page transitions
- ✅ Input focus animations
- ✅ Button hover effects
- ✅ Loading spinners
- ✅ Success checkmarks
- ✅ Error shake effects
- ✅ Gradient shifts
- ✅ Micro-interactions

## 📦 Tech Stack

- **Framework**: Next.js 14
- **UI Library**: React 18
- **Styling**: Tailwind CSS 3.3
- **Animations**: Framer Motion 10
- **Icons**: React Icons 5
- **Language**: JavaScript (can be TypeScript)

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ installed
- npm 9+ installed

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Edit .env.local with your API URL
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🎨 Component Structure

```
frontend/src/
├── components/
│   ├── SupportForm.jsx          # Main form component (500+ lines)
│   ├── LanguageSwitcher.jsx     # Animated language selector
│   ├── StatusDisplay.jsx        # Ticket status with timeline
│   └── FormValidation.js        # Validation logic
├── pages/
│   ├── index.jsx                # Home page
│   ├── _app.jsx                 # App wrapper
│   └── _document.jsx            # HTML document
├── services/
│   └── api.js                   # Backend API client
├── utils/
│   └── translations.js          # Multi-language translations (6 languages)
└── styles/
    ├── globals.css              # Global styles + Tailwind
    └── support-form.css         # Custom animations
```

## 🌍 Language Support

### Adding a New Language

1. Open `src/utils/translations.js`
2. Add your language to the `translations` object:

```javascript
export const translations = {
  // ... existing languages
  de: {
    title: "Kundensupport",
    subtitle: "Wir sind 24/7 für Sie da",
    // ... add all translations
  }
};
```

3. Add to `languages` array:

```javascript
export const languages = [
  // ... existing languages
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' }
];
```

### RTL (Right-to-Left) Support

For RTL languages (Urdu, Arabic), add `rtl: true`:

```javascript
{ code: 'ar', name: 'العربية', flag: '🇸🇦', rtl: true }
```

## 🎯 Form Validation

### Client-Side Validation Rules

- **Name**: Minimum 2 characters
- **Email**: Valid email format (RFC 5322)
- **Message**: Minimum 10 characters
- **Input Sanitization**: XSS protection

### Validation Functions

```javascript
import { validateForm, validateEmail, validateName, validateMessage } from './components/FormValidation';

const { isValid, errors } = validateForm(formData, translations);
```

## 🔌 API Integration

### Backend Endpoints

```javascript
// Submit support form
POST /api/webhooks/web
Body: { name, email, message }
Response: { ticket_id, status, message }

// Check ticket status
GET /api/tickets/{ticket_id}/status
Response: { ticket_id, status, response, created_at, updated_at }
```

### API Client Usage

```javascript
import { api } from '../services/api';

// Submit form
const result = await api.submitSupportForm({
  name: "John Doe",
  email: "john@example.com",
  message: "How can I reset my password?"
});

// Check status
const status = await api.checkTicketStatus(ticketId);
```

## 🎨 Customization

### Colors & Gradients

Edit `tailwind.config.js` to customize colors:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        500: '#6366f1', // Indigo
        600: '#4f46e5',
      }
    }
  }
}
```

### Animations

Modify animations in `src/styles/support-form.css`:

```css
@keyframes custom-animation {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}
```

## 📱 Responsive Design

Breakpoints:
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

All components are fully responsive with Tailwind's responsive utilities:

```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
```

## ✨ Key Features Explained

### 1. Language Switcher
- Animated dropdown with flags
- Instant language switching
- Persistent selection (can add localStorage)
- Beautiful hover effects

### 2. Form Validation
- Real-time validation as user types
- Clear error messages in selected language
- Visual feedback (red borders, shake animations)
- Submit button disabled during submission

### 3. Status Display
- Animated timeline showing ticket progress
- Color-coded status badges
- Spinning icons for "processing" state
- Timestamps for created/updated dates

### 4. Animations
- **Framer Motion** for smooth transitions
- **Gradient animations** on background
- **Hover effects** on buttons/cards
- **Loading spinners** during API calls
- **Success/Error alerts** with slide-in animations

## 🧪 Testing

### Run Tests

```bash
# Unit tests
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

### Testing Strategy

- Component rendering tests
- Form validation tests
- API integration tests
- Multi-language tests
- Accessibility tests

## 🚀 Production Build

```bash
# Build for production
npm run build

# Start production server
npm start

# The app will be optimized and minified
```

### Build Optimizations

- ✅ Code splitting
- ✅ Image optimization
- ✅ CSS minification
- ✅ Tree shaking
- ✅ Compression enabled

## 📊 Performance

### Lighthouse Scores (Target)

- **Performance**: 95+
- **Accessibility**: 100
- **Best Practices**: 100
- **SEO**: 100

### Optimization Features

- Lazy loading components
- Image optimization with Next.js
- CSS purging with Tailwind
- Minified JavaScript
- GZIP compression

## 🎯 Usage Examples

### Basic Form Submission

```jsx
<SupportForm />
```

That's it! The component handles everything internally.

### Custom Styling

```jsx
<SupportForm className="custom-class" />
```

### Embedding in Website

```html
<!-- Option 1: iframe -->
<iframe src="http://localhost:3000" width="100%" height="800px"></iframe>

<!-- Option 2: Component import (if using React) -->
<SupportForm />
```

## 🔒 Security

- ✅ Input sanitization (XSS protection)
- ✅ CSRF token validation (to be added in backend)
- ✅ Rate limiting (backend)
- ✅ No sensitive data in frontend
- ✅ HTTPS recommended for production

## 🌐 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Docker

```bash
# Build Docker image
docker build -t digital-fte-web .

# Run container
docker run -p 3000:3000 digital-fte-web
```

### Environment Variables

Set in deployment:
```
NEXT_PUBLIC_API_URL=https://api.yourcompany.com
```

## 📝 Changelog

### Version 1.0.0 (2026-03-14)

- ✅ Initial release
- ✅ Multi-language support (6 languages)
- ✅ Framer Motion animations
- ✅ Tailwind CSS styling
- ✅ Form validation
- ✅ Ticket status checking
- ✅ RTL support for Urdu/Arabic
- ✅ Responsive design
- ✅ API integration

## 🤝 Contributing

This is a hackathon project for the Digital FTE Customer Success Agent.

## 📄 License

Built as part of "The CRM Digital FTE Factory" hackathon challenge.

---

**Built with** ❤️ **using Next.js, Framer Motion, and Tailwind CSS**

**Developed by**: Digital FTE Team
**Date**: 2026-03-14
**Status**: ✅ Production Ready (MANDATORY Deliverable Complete)
