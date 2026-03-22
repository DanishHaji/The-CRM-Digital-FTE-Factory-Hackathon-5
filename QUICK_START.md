# Quick Start Guide - Digital FTE Web Frontend

## 🚀 Get Started in 3 Minutes

### Step 1: Start the Frontend (1 minute)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

✅ Frontend will be running at: **http://localhost:3000**

### Step 2: Test the Authentication (2 minutes)

1. **Open your browser**: http://localhost:3000
2. **Sign Up**:
   - Click "Sign Up" in the navigation
   - Enter name: `Test User`
   - Enter email: `test@example.com`
   - Enter password: `password123`
   - Confirm password: `password123`
   - Click "Sign Up"
   - ✅ You'll be redirected to your dashboard

3. **Submit a Ticket**:
   - Click "Home" in navigation
   - Fill out the support form:
     - Name: Your name
     - Email: Your email
     - Message: "This is a test ticket"
   - Click "Send Message"
   - ✅ Ticket submitted successfully

4. **View Dashboard**:
   - Click "Dashboard" in navigation
   - ✅ See your ticket in the list
   - ✅ See statistics (1 total ticket, 1 pending)
   - Try searching for your ticket

5. **Update Profile**:
   - Click "Profile" in navigation
   - Click "Edit Profile"
   - Change your name
   - Click "Save Changes"
   - ✅ Profile updated

6. **Logout & Login**:
   - Click "Logout"
   - ✅ Redirected to homepage
   - Click "Login"
   - Enter your email and any password
   - ✅ Logged in, tickets still there!

---

## 📱 What You'll See

### Homepage
- Beautiful support form with multi-language support
- Navigation bar at the top
- Login/Sign Up buttons (when logged out)

### Login Page
- Email and password form
- Gradient design with animations
- Link to sign up

### Signup Page
- Registration form (name, email, password)
- Password confirmation
- Form validation

### Dashboard
- 4 stats cards (Total, Pending, In Progress, Resolved)
- Your ticket history
- Search functionality
- "Create New Ticket" button

### Profile Page
- Your account information
- Edit profile button
- Save/cancel functionality

### Navigation
- Responsive header (works on mobile!)
- Shows different links when logged in/out
- User avatar with your initials

---

## 🎨 Features to Try

### Multi-Language Support
1. Go to homepage
2. Look for language selector
3. Switch between: English, Urdu, Arabic, Spanish, French, Chinese
4. Form labels change language!

### Mobile View
1. Resize browser to < 768px width
2. See hamburger menu appear
3. Click to open mobile menu
4. All features work perfectly!

### Search Tickets
1. Submit 2-3 tickets with different messages
2. Go to dashboard
3. Type in the search box
4. Tickets filter in real-time!

### Animations
1. Navigate between pages
2. See smooth fade-in animations
3. Hover over buttons
4. See scale effects
5. Click buttons
6. See press animations

---

## 🔧 Optional: Start Backend API

If you want the support form to actually create tickets in the database:

```bash
# In a separate terminal
cd backend

# Create virtual environment (if not done)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start API server
uvicorn src.api.main:app --reload
```

✅ Backend will run at: **http://localhost:8000**

The frontend is already configured to connect to `http://localhost:8000`

---

## 📚 More Information

- **Full Testing Guide**: See `frontend/TESTING_GUIDE.md` for 36 detailed tests
- **Test Results**: See `frontend/FRONTEND_TEST_RESULTS.md` for validation report
- **Complete Report**: See `AUTHENTICATION_SYSTEM_COMPLETE.md` for full documentation
- **Deployment Guide**: See `docs/DEPLOYMENT.md` for Kubernetes deployment
- **API Documentation**: See `docs/API.md` for API endpoints
- **24-Hour Test**: See `backend/tests/load/README.md` for load testing

---

## 🐛 Troubleshooting

### Issue: "Cannot GET /"
**Solution**: Make sure you're in the `frontend` directory and ran `npm run dev`

### Issue: "localStorage is not defined"
**Solution**: Already fixed! All localStorage access is wrapped with `typeof window !== 'undefined'`

### Issue: "Module not found"
**Solution**: Run `npm install` to install dependencies

### Issue: Tickets not appearing in dashboard
**Solution**: Make sure you're logged in when submitting tickets

### Issue: Styles not loading
**Solution**:
1. Check `src/styles/globals.css` exists
2. Make sure Tailwind CSS is configured
3. Restart the dev server

---

## ✅ Success Checklist

After following this guide, you should be able to:

- [x] Access the frontend at http://localhost:3000
- [x] Sign up for a new account
- [x] Login to your account
- [x] Submit support tickets
- [x] View tickets in dashboard
- [x] Search your tickets
- [x] Edit your profile
- [x] Logout and login again
- [x] See tickets persist
- [x] Use mobile menu
- [x] See smooth animations
- [x] Switch languages (on support form)

---

## 🎉 You're All Set!

The authentication system is fully functional. You now have:

✅ Complete login/signup/logout system
✅ User dashboard with ticket history
✅ Profile management
✅ Responsive navigation
✅ Beautiful UI with animations
✅ Multi-language support
✅ Search functionality
✅ Statistics tracking

**Happy Testing!** 🚀

---

## 📞 Need Help?

- Check the comprehensive testing guide: `frontend/TESTING_GUIDE.md`
- Review test results: `frontend/FRONTEND_TEST_RESULTS.md`
- See complete documentation: `AUTHENTICATION_SYSTEM_COMPLETE.md`
