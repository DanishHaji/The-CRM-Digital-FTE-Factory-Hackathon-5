# Frontend Testing Guide

## Quick Start

### 1. Install Dependencies (if not already done)
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

The application will be available at: http://localhost:3000

## Testing the Authentication System

### Test 1: User Signup
1. Open http://localhost:3000
2. Click "Sign Up" button in the navigation
3. Fill out the form:
   - Name: Test User
   - Email: test@example.com
   - Password: password123
   - Confirm Password: password123
4. Click "Sign Up"
5. **Expected**: Redirected to dashboard

### Test 2: User Logout
1. While logged in, click your profile in the navigation
2. Click "Logout"
3. **Expected**: Redirected to homepage, navigation shows "Login" and "Sign Up"

### Test 3: User Login
1. Click "Login" in navigation
2. Enter:
   - Email: test@example.com (or the email you signed up with)
   - Password: anything (password not validated in MVP)
3. Click "Sign In"
4. **Expected**: Redirected to dashboard

### Test 4: Protected Routes
1. Logout if logged in
2. Try to navigate directly to http://localhost:3000/dashboard
3. **Expected**: Redirected to login page
4. Try to navigate to http://localhost:3000/profile
5. **Expected**: Redirected to login page

## Testing the Support Form

### Test 5: Submit Support Ticket (Not Logged In)
1. Logout if logged in
2. Go to homepage
3. Fill out support form:
   - Name: John Doe
   - Email: john@example.com
   - Message: I need help with my account
4. Click "Send Message"
5. **Expected**: Success message appears, ticket ID shown
6. **Note**: Ticket will NOT be saved to dashboard (user not logged in)

### Test 6: Submit Support Ticket (Logged In)
1. Login to your account
2. Go to homepage
3. Fill out support form:
   - Name: Test User
   - Email: test@example.com
   - Message: This is a test ticket
4. Click "Send Message"
5. **Expected**: Success message appears
6. Click "Dashboard" in navigation
7. **Expected**: Your ticket appears in the list

### Test 7: View Ticket in Dashboard
1. Login and go to dashboard
2. **Expected**: See stats cards showing:
   - Total Tickets
   - Pending
   - In Progress
   - Resolved
3. **Expected**: See your submitted tickets in the list
4. **Expected**: Each ticket shows status badge

### Test 8: Search Tickets
1. Go to dashboard with multiple tickets
2. Type in the search box
3. **Expected**: Tickets filter in real-time

## Testing the Profile Page

### Test 9: View Profile
1. Login
2. Click "Profile" in navigation
3. **Expected**: See your user information:
   - Name
   - Email
   - Account created date
   - User ID

### Test 10: Edit Profile
1. On profile page, click "Edit Profile"
2. Change your name to "Updated Name"
3. Click "Save Changes"
4. **Expected**: Success message appears
5. **Expected**: Page reloads with updated name
6. **Expected**: Navigation shows updated name

### Test 11: Cancel Edit
1. Click "Edit Profile"
2. Change the name
3. Click "Cancel"
4. **Expected**: Edit mode closes, changes discarded

## Testing the Navigation

### Test 12: Mobile Navigation
1. Resize browser to mobile size (< 768px width)
2. **Expected**: Hamburger menu icon appears
3. Click hamburger menu
4. **Expected**: Mobile menu slides out
5. Click any link
6. **Expected**: Menu closes, navigation occurs

### Test 13: Navigation Links (Logged Out)
1. Logout
2. **Expected**: Navigation shows:
   - Home
   - Login
   - Sign Up

### Test 14: Navigation Links (Logged In)
1. Login
2. **Expected**: Navigation shows:
   - Home
   - Dashboard
   - Profile
   - Logout
   - User avatar/name

## Testing Multi-Language Support

### Test 15: Language Switcher (on Support Form)
1. Go to homepage
2. Look for language selector
3. **Expected**: Can switch between languages:
   - English
   - Urdu
   - Arabic
   - Spanish
   - French
   - Chinese
4. Select a language
5. **Expected**: Form labels change to selected language

## Testing Form Validation

### Test 16: Login Form Validation
1. Go to login page
2. Try to submit empty form
3. **Expected**: Error message "Please fill in all fields"
4. Enter invalid email: "notanemail"
5. **Expected**: Error message "Please enter a valid email address"

### Test 17: Signup Form Validation
1. Go to signup page
2. Try to submit with password < 6 characters
3. **Expected**: Error "Password must be at least 6 characters long"
4. Enter different passwords in password and confirm
5. **Expected**: Error "Passwords do not match"

### Test 18: Support Form Validation
1. Go to homepage
2. Try to submit empty form
3. **Expected**: Validation errors appear
4. Enter invalid email
5. **Expected**: Email validation error

## Testing Responsive Design

### Test 19: Desktop View (> 1024px)
1. Maximize browser window
2. Check all pages:
   - Homepage
   - Login
   - Signup
   - Dashboard
   - Profile
3. **Expected**: Full navigation bar, proper spacing, multi-column layouts

### Test 20: Tablet View (768px - 1024px)
1. Resize to tablet width
2. Check all pages
3. **Expected**: Adjusted layouts, still horizontal navigation

### Test 21: Mobile View (< 768px)
1. Resize to mobile width
2. Check all pages
3. **Expected**:
   - Hamburger menu
   - Single column layouts
   - Touch-friendly buttons
   - Readable text

## Testing Error Handling

### Test 22: Network Error (Backend Down)
1. Stop the backend API if running
2. Try to submit a support form
3. **Expected**: Error message appears:
   - "Network error. Please check your connection."
   OR
   - "Failed to submit form"

### Test 23: Invalid Ticket ID
1. Go to homepage
2. Use ticket status checker
3. Enter invalid ticket ID: "INVALID123"
4. Click check status
5. **Expected**: Error message appears

## Testing Session Persistence

### Test 24: Page Refresh While Logged In
1. Login to your account
2. Refresh the page (F5 or Ctrl+R)
3. **Expected**: Still logged in, user info persists
4. Navigate to dashboard
5. **Expected**: Tickets still visible

### Test 25: Browser Close/Open
1. Login to your account
2. Close the browser completely
3. Reopen browser and go to http://localhost:3000
4. **Expected**: Still logged in (localStorage persists)

### Test 26: Multiple Tabs
1. Login in one tab
2. Open a new tab to http://localhost:3000
3. **Expected**: Also logged in (shared localStorage)
4. Logout in one tab
5. **Expected**: Other tab updates on refresh

## Testing Animations

### Test 27: Page Transitions
1. Navigate between pages
2. **Expected**: Smooth fade-in animations
3. **Expected**: No jarring transitions

### Test 28: Button Interactions
1. Hover over buttons
2. **Expected**: Scale animation on hover
3. Click buttons
4. **Expected**: Scale down animation on click

### Test 29: Form Submission Loading
1. Submit a form
2. **Expected**: Loading indicator appears
3. **Expected**: Button disabled during submission
4. **Expected**: "Submitting..." or similar text

## Testing Edge Cases

### Test 30: Very Long Ticket Message
1. Submit a ticket with 1000+ character message
2. **Expected**: Ticket submits successfully
3. Check dashboard
4. **Expected**: Message truncated in list view

### Test 31: Special Characters in Input
1. Submit form with special characters: `<script>alert('test')</script>`
2. **Expected**: Characters sanitized/escaped
3. **Expected**: No script execution

### Test 32: Empty Dashboard
1. Login with a brand new account
2. Go to dashboard
3. **Expected**: Empty state shown
4. **Expected**: Message "No tickets found"
5. **Expected**: "Create your first support ticket" prompt

## Common Issues & Solutions

### Issue 1: "localStorage is not defined"
**Cause**: Accessing localStorage during server-side rendering
**Solution**: Already fixed with `typeof window !== 'undefined'` checks

### Issue 2: Page doesn't redirect after login
**Cause**: useRouter not working
**Check**:
- Is Next.js router imported?
- Is component wrapped in AuthProvider?

### Issue 3: Tickets not appearing in dashboard
**Cause**: User email mismatch
**Check**:
- Are you logged in?
- Did you submit the ticket while logged in?
- Check browser console for errors

### Issue 4: Styles not loading
**Cause**: CSS files not imported
**Check**:
- Is globals.css imported in _app.jsx?
- Is Tailwind CSS configured correctly?

### Issue 5: API connection errors
**Cause**: Backend not running
**Solution**:
```bash
# Start backend in separate terminal
cd ../backend
uvicorn src.api.main:app --reload
```

## Performance Testing

### Test 33: Page Load Speed
1. Open browser dev tools (F12)
2. Go to Network tab
3. Hard refresh (Ctrl+Shift+R)
4. **Expected**: Page loads in < 2 seconds on localhost

### Test 34: Navigation Speed
1. Click through all pages
2. **Expected**: Instant navigation (Next.js client-side routing)
3. **Expected**: No full page reloads

## Accessibility Testing

### Test 35: Keyboard Navigation
1. Use Tab key to navigate
2. **Expected**: Can reach all interactive elements
3. **Expected**: Focus indicators visible
4. Press Enter on buttons
5. **Expected**: Actions trigger

### Test 36: Screen Reader (if available)
1. Enable screen reader
2. Navigate through pages
3. **Expected**: Form labels read aloud
4. **Expected**: Button purposes clear

## Final Checklist

Before considering testing complete:

- [ ] All 36 tests passed
- [ ] No console errors in browser
- [ ] No console warnings (or only minor ones)
- [ ] All animations smooth
- [ ] All forms validate correctly
- [ ] All navigation works
- [ ] Mobile view works perfectly
- [ ] Session persists across refreshes
- [ ] LocalStorage working correctly
- [ ] Ready for production (with backend API)

## Reporting Issues

If you find any issues during testing:

1. Note the test number
2. Describe what you expected
3. Describe what actually happened
4. Include browser console errors (F12 → Console)
5. Include screenshots if relevant
6. Note browser version and OS

## Next Steps After Testing

Once all tests pass:

1. ✅ Frontend is ready for development use
2. 🔄 Connect to backend API (replace localStorage calls)
3. 🔒 Implement proper authentication (JWT tokens)
4. 🚀 Deploy to production
5. 📊 Set up analytics
6. 🔍 Set up error monitoring (Sentry, etc.)

---

**Happy Testing! 🎉**
