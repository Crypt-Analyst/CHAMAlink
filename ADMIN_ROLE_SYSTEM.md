# ChamaLink - Admin & Member Role System

## 🎯 Role-Based Access Control System

### 1. **Role Hierarchy**
- **Creator**: The first person who creates a chama
- **Admin**: Appointed by the creator to help manage the chama
- **Member**: Regular chama participants

### 2. **Creator Powers**
- ✅ **Cannot be removed** from the chama
- ✅ **Can make members admins** (promote to admin role)
- ✅ **Can remove any member** except themselves
- ✅ **Can edit chama settings** (name, description, fees)
- ✅ **Can approve/reject join requests**
- ✅ **Can approve/reject loans**
- ✅ **Can assign penalties**
- ✅ **Full financial oversight**

### 3. **Admin Powers**
- ✅ **Can remove regular members** (not creator or other admins)
- ✅ **Can approve/reject join requests**
- ✅ **Can approve/reject loans**
- ✅ **Can assign penalties**
- ✅ **Can view member details**
- ❌ **Cannot remove creator**
- ❌ **Cannot make other admins**
- ❌ **Cannot edit chama settings**

### 4. **Member Powers**
- ✅ **Can apply for loans**
- ✅ **Can make contributions**
- ✅ **Can pay penalties**
- ✅ **Can view chama information**
- ✅ **Can request to leave chama**
- ❌ **Cannot remove other members**
- ❌ **Cannot approve anything**
- ❌ **Cannot assign penalties**

## 🚀 **New User Journey**

### 1. **First User (Chama Creator)**
```
Register → Create Chama → Become Creator → Invite 2 Admins → Manage Chama
```

### 2. **Subsequent Users**
```
Register → Search Chamas → Request to Join → Admin Approval → Pay Registration Fee → Become Member
```

## 📱 **Mobile App View Differentiation**

### **Creator View**
- **Dashboard**: Full chama statistics, member management panel
- **Members Page**: Can remove members, make admins, view all details
- **Settings**: Can edit chama name, description, registration fee
- **Approvals**: Can approve/reject all requests
- **Financial**: Can approve loans, assign penalties

### **Admin View**
- **Dashboard**: Chama statistics, limited member management
- **Members Page**: Can remove regular members, view details
- **Settings**: View-only chama settings
- **Approvals**: Can approve/reject member requests and loans
- **Financial**: Can approve loans, assign penalties

### **Member View**
- **Dashboard**: Basic chama information, personal statistics
- **Members Page**: View-only member list
- **Settings**: Personal settings only
- **Approvals**: Can see own requests status
- **Financial**: Can apply for loans, pay penalties

## 🔧 **Technical Implementation**

### **Role Check Functions**
```python
# Check if user is admin
chama.is_admin(user_id)

# Check if admin can remove specific member
chama.can_remove_member(admin_user_id, target_user_id)

# Get all admins
chama.admins

# Get regular members
chama.regular_members
```

### **Template Conditionals**
```html
{% if user_role == 'creator' %}
    <!-- Creator-only features -->
{% elif user_role == 'admin' %}
    <!-- Admin features -->
{% else %}
    <!-- Member features -->
{% endif %}
```

### **Route Protection**
```python
@chama_admin_required  # Only admins and creator
@chama_member_required  # All chama members
```

## 🎯 **Search & Join System**

### **How It Works**
1. **User searches** for chamas by name
2. **System shows** available chamas (excluding ones user is already in)
3. **User clicks** "Request to Join"
4. **System sends** notification to all chama admins
5. **Admins review** and approve/reject request
6. **If approved**, user pays registration fee
7. **User becomes** full member after payment

### **Admin Approval Process**
- **3-admin approval** required for sensitive actions
- **Notifications** sent to all admins
- **Email notifications** for important actions
- **Audit trail** of all approvals

## 📊 **Member Management Features**

### **For Admins**
- **Remove Members**: Click "Remove" button on member row
- **Make Admin**: Creator can promote members to admin
- **View Details**: See member contact information
- **Track Activity**: View member contribution history

### **For Members**
- **View Members**: See all chama members and their roles
- **Contact Info**: Basic member contact details
- **Role Badges**: Clear visual indicators of member roles

## 🔒 **Security Features**

### **Protection Measures**
- **Creator cannot be removed** by anyone
- **Admins cannot remove other admins**
- **Role-based view restrictions**
- **Permission checks** on all admin actions
- **Audit logging** of all member changes

### **Data Privacy**
- **Members see** basic member information
- **Admins see** detailed member information
- **Creator sees** all member information
- **Financial data** restricted by role

## 📱 **Mobile App Considerations**

### **UI/UX Differences**
- **Different button sets** based on role
- **Conditional menus** and navigation
- **Role-specific dashboards**
- **Permission-based feature access**

### **Performance Optimization**
- **Lazy loading** of admin features
- **Cached role checks**
- **Optimized queries** for role-based data
- **Progressive enhancement** for admin features

This system ensures proper hierarchy, security, and user experience while providing clear differentiation between roles in both web and mobile applications.
