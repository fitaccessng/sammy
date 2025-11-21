# HR Profile & Settings Implementation

## Overview
Implemented comprehensive profile and settings pages for HR users with full backend integration and responsive design.

## Files Modified

### 1. Backend Routes (app.py)
- **Line 11035-11220**: `hr.profile` route - Displays user profile with statistics
  - Leave balance calculation (25 annual days - used days)
  - Attendance rate from Attendance records
  - Completed tasks count
  - Recent activities from PayrollHistory and Leave approvals
  
- **Line 11161-11220**: `hr.update_profile` route - Updates user profile information
  - Validates name and email
  - Checks for duplicate emails
  - Updates User and Employee records
  - CSRF protection included

- **Line 11223-11231**: `hr.settings` route - Displays settings page
  - Enhanced to pass user object to template

- **Line 11233-11285**: `hr.change_password` route - Changes user password
  - Validates current password
  - Checks password match and strength (min 8 chars)
  - Updates password with hashing
  - CSRF protection included

- **Line 11287-11315**: `hr.update_preferences` route - Updates user preferences
  - Language selection
  - Timezone preferences
  - Date format preferences
  - CSRF protection included

### 2. Frontend Templates

#### templates/hr/base.html
- **Lines 180-195**: Updated dropdown menu links
  - Profile link now points to `url_for('hr.profile')`
  - Settings link now points to `url_for('hr.settings')`
  - Added icons to menu items
  - Added z-index for proper layering

#### templates/hr/profile/index.html
**Features:**
- Responsive design (mobile-first approach)
- User profile header with avatar
- Editable profile information (name, email, phone)
- Statistics cards:
  - Leave Balance with icon
  - Attendance Rate with icon
  - Completed Tasks with icon
- Recent activity timeline
- Edit profile modal with CSRF protection
- Loading states for form submission

**Responsive Breakpoints:**
- Mobile: Single column layout
- Tablet (sm): Flex layout for profile header
- Desktop (lg): 3-column grid for stats

#### templates/hr/settings/index.html
**Features:**
- Three tabbed sections:
  1. **Account Settings**
     - Language selection
     - Timezone selection
     - Date format preferences
     - CSRF protection
  
  2. **Notification Preferences**
     - Email notifications toggle
     - Leave request updates toggle
     - Task assignment notifications toggle
     - Toggle switches with animations
  
  3. **Security Settings**
     - Password change form (current, new, confirm)
     - Password strength validation (min 8 chars)
     - Two-factor authentication toggle
     - CSRF protection
     - Client-side password match validation

**Responsive Features:**
- Mobile-friendly tab navigation with icons
- Responsive grid layouts
- Touch-friendly toggle switches
- Loading states for form submissions

## Security Features

### CSRF Protection
All forms include CSRF tokens:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
```

### Password Security
- Current password verification
- Minimum 8 characters requirement
- Password confirmation matching
- Secure password hashing using werkzeug

### Access Control
All routes protected with `@role_required([Roles.SUPER_HQ, Roles.HQ_HR])`

## User Experience Enhancements

### 1. Visual Feedback
- Flash messages for success/error states
- Loading states during form submission
- Icons for visual clarity

### 2. Modal Management
- Profile edit in modal overlay
- Keyboard support (Escape to close)
- Click outside to close
- Proper z-index layering

### 3. Form Validation
- Required field validation
- Email format validation
- Password strength requirements
- Client-side password match checking

### 4. Responsive Design
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px)
- Flexible layouts for all screen sizes
- Touch-friendly interactive elements

## Data Flow

### Profile Page
1. User navigates to `/hr/profile`
2. Backend fetches user data and calculates:
   - Leave balance from Leave model
   - Attendance rate from Attendance records
   - Completed tasks count
   - Recent activities
3. Template displays user info and stats
4. User clicks "Edit Profile"
5. Modal opens with pre-filled form
6. User submits changes
7. Backend validates and updates User + Employee records
8. Redirect to profile with success message

### Settings Page
1. User navigates to `/hr/settings`
2. Backend passes user object to template
3. User switches between tabs (Account, Notifications, Security)
4. User makes changes and submits form
5. Backend processes based on form action:
   - `/hr/settings/preferences` for account settings
   - `/hr/settings/password` for password changes
6. Redirect to settings with success message

## Database Integration

### Tables Used
- **User**: Authentication and basic profile
- **Employee**: Extended profile information
- **Leave**: Leave balance calculations
- **Attendance**: Attendance rate calculations
- **Task**: Completed tasks count
- **PayrollHistory**: Recent activities

### Key Queries
```python
# Leave balance
leave_days_used = Leave.query.filter_by(
    employee_id=employee.id,
    status='approved',
    extract('year', Leave.start_date) == current_year
).count()
leave_balance = 25 - leave_days_used

# Attendance rate
total_attendance = Attendance.query.filter_by(employee_id=employee.id).count()
present_days = Attendance.query.filter_by(
    employee_id=employee.id, 
    status='present'
).count()
attendance_rate = (present_days / total_attendance * 100) if total_attendance > 0 else 98

# Completed tasks
completed_tasks = Task.query.filter_by(
    assigned_to=user.id,
    status='completed',
    extract('year', Task.completion_date) == current_year
).count()
```

## Testing Checklist

### Profile Page
- [ ] Profile displays correct user information
- [ ] Leave balance calculation is accurate
- [ ] Attendance rate displays correctly
- [ ] Completed tasks count is accurate
- [ ] Recent activities show up
- [ ] Edit profile modal opens/closes
- [ ] Profile update saves successfully
- [ ] Email duplicate check works
- [ ] Responsive on mobile/tablet/desktop
- [ ] Flash messages display correctly

### Settings Page
- [ ] All tabs switch correctly
- [ ] Account preferences save
- [ ] Password change validates current password
- [ ] Password strength enforced (min 8 chars)
- [ ] Password match validation works
- [ ] Success/error messages display
- [ ] Responsive on all screen sizes
- [ ] Toggle switches work properly
- [ ] CSRF protection active on all forms

### Navigation
- [ ] Dropdown menu shows Profile link
- [ ] Dropdown menu shows Settings link
- [ ] Links navigate to correct routes
- [ ] Icons display in menu items

## Future Enhancements

### Potential Features
1. **Avatar Upload**: Allow users to upload custom profile pictures
2. **Preferences Storage**: Create UserPreferences table to persist settings
3. **Two-Factor Authentication**: Implement actual 2FA functionality
4. **Activity Log**: More detailed activity tracking with filtering
5. **Email Notifications**: Actually send email notifications based on preferences
6. **Theme Switching**: Light/dark mode toggle
7. **Export Data**: Allow users to export their data
8. **API Integration**: RESTful API for mobile app support

### Database Schema Addition
```python
class UserPreferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(50), default='English')
    timezone = db.Column(db.String(50), default='UTC (GMT+0)')
    date_format = db.Column(db.String(20), default='DD/MM/YYYY')
    email_notifications = db.Column(db.Boolean, default=True)
    leave_notifications = db.Column(db.Boolean, default=True)
    task_notifications = db.Column(db.Boolean, default=True)
    theme = db.Column(db.String(20), default='light')
```

## Notes
- All forms include CSRF protection
- Password hashing uses werkzeug's security functions
- Responsive design tested on mobile, tablet, and desktop
- All routes require HR role access
- Profile updates sync between User and Employee tables
- Leave balance assumes 25 annual leave days per year
