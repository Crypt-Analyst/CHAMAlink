# 🔐 QUICKBOOKS ACCESS CONTROL & ROLE PERMISSIONS

## 🎯 Who Can Access QuickBooks Integration?

Based on your CHAMAlink leadership system, here's exactly who can see and use QuickBooks features:

## 👥 **CURRENT ACCESS LEVELS** (As Implemented)

### ✅ **FULL ACCESS** - Can Connect & Manage QuickBooks
- **🏆 Creator** (Permanent role, full admin access)
- **👑 System Admin** (Platform administrators)

### ❌ **NO DIRECT ACCESS** - Cannot Connect QuickBooks
- **📊 Treasurer** (Can see financial data, but not QuickBooks connection)
- **📝 Secretary** (Handles communications, no QuickBooks access)  
- **👥 Members** (Basic access only)

## 🔧 **RECOMMENDED ROLE-BASED ACCESS** (Suggested Enhancement)

Here's how QuickBooks access should be configured for optimal chama management:

### **Level 1: Connection Management** (Who can connect/disconnect QuickBooks)
```
✅ Creator (Permanent)
✅ Chairperson (If creator delegates)
❌ Treasurer (Cannot connect, but should see sync status)
❌ Secretary (No QuickBooks access needed)
❌ Members (No access)
```

### **Level 2: Financial Sync Access** (Who can sync financial data)
```
✅ Creator (Full sync control)
✅ Treasurer (Should sync financial data)
❌ Secretary (No financial sync access)
❌ Members (No sync access)
```

### **Level 3: View-Only Access** (Who can see QuickBooks status)
```
✅ Creator (Full visibility)
✅ Chairperson (Full visibility)
✅ Treasurer (Financial sync status only)
✅ Secretary (Basic connection status)
❌ Members (No QuickBooks visibility)
```

## 🛠️ **IMPLEMENTING TREASURER QUICKBOOKS ACCESS**

To give treasurers appropriate QuickBooks access, you need to update the integration routes:

### **Step 1: Create Role-Based Decorators**

Create `app/routes/decorators.py`:

```python
from functools import wraps
from flask import abort
from flask_login import current_user
from app.models import ChamaMember

def treasurer_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        
        # Check if user is treasurer of any chama
        chama_id = kwargs.get('chama_id')
        if chama_id:
            membership = ChamaMember.query.filter_by(
                user_id=current_user.id,
                chama_id=chama_id
            ).first()
            
            if membership and membership.role in ['creator', 'treasurer']:
                return f(*args, **kwargs)
        
        abort(403)
    return decorated_function

def financial_role_required(f):
    """Allow creator, chairperson, or treasurer"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        
        chama_id = kwargs.get('chama_id')
        if chama_id:
            membership = ChamaMember.query.filter_by(
                user_id=current_user.id,
                chama_id=chama_id
            ).first()
            
            if membership and membership.role in ['creator', 'chairperson', 'treasurer']:
                return f(*args, **kwargs)
        
        abort(403)
    return decorated_function
```

### **Step 2: Update QuickBooks Routes with Role-Based Access**

Update `app/routes/integrations.py`:

```python
from app.routes.decorators import treasurer_or_admin_required, financial_role_required

# Connection management (Creator/Admin only)
@integrations_bp.route('/accounting/quickbooks/oauth')
@login_required
@admin_required  # Keep admin-only for connection
def quickbooks_oauth():
    # ... existing code ...

# Sync operations (Treasurer can sync)
@integrations_bp.route('/sync/quickbooks/<int:chama_id>')
@login_required
@financial_role_required  # Creator, Chairperson, or Treasurer
def sync_quickbooks_chama(chama_id):
    # ... existing code ...

# View sync status (Treasurer can view)
@integrations_bp.route('/quickbooks/status/<int:chama_id>')
@login_required
@treasurer_or_admin_required  # Creator or Treasurer
def quickbooks_status(chama_id):
    # Return QuickBooks connection and sync status
    # ... implementation ...
```

## 📊 **DASHBOARD ACCESS BY ROLE**

### **Creator Dashboard** (Full QuickBooks Management)
- ✅ Connect/disconnect QuickBooks
- ✅ View all chama integrations
- ✅ Manual sync all chamas
- ✅ View detailed sync logs
- ✅ Test connections
- ✅ Configure sync settings

### **Treasurer Dashboard** (Financial Sync Focus)
- ❌ Cannot connect/disconnect QuickBooks
- ✅ View QuickBooks connection status
- ✅ Sync their chama's financial data
- ✅ View sync history for their chama
- ✅ See sync success/failure notifications
- ❌ Cannot access other chamas' data

### **Secretary Dashboard** (Basic Status Only)
- ❌ Cannot connect QuickBooks
- ❌ Cannot sync data
- ✅ View basic connection status (connected/not connected)
- ❌ Cannot access detailed sync information

### **Member Dashboard** (No QuickBooks Access)
- ❌ No QuickBooks features visible
- ❌ Cannot see integration status
- ❌ No sync capabilities

## 🎨 **CUSTOMIZED UI BY ROLE**

### **For Treasurers** - Add to Chama Dashboard:

```html
<!-- Treasurer's QuickBooks Section -->
{% if current_user_role in ['creator', 'treasurer'] %}
<div class="card border-0 shadow-sm mb-4">
    <div class="card-header bg-light">
        <h5 class="card-title mb-0">
            <i class="fab fa-quickbooks text-primary"></i> QuickBooks Integration
        </h5>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-8">
                <div id="quickbooks-status-display">
                    <div class="d-flex align-items-center">
                        <div class="status-indicator me-3">
                            <span class="badge badge-success">Connected</span>
                        </div>
                        <div>
                            <h6 class="mb-1">Professional Accounting Active</h6>
                            <small class="text-muted">Last sync: 2 hours ago</small>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4 text-end">
                {% if current_user_role == 'creator' %}
                <button class="btn btn-outline-primary btn-sm me-2" onclick="openQuickBooksSettings()">
                    <i class="fas fa-cog"></i> Settings
                </button>
                {% endif %}
                <button class="btn btn-primary btn-sm" onclick="syncToQuickBooks({{ chama.id }})">
                    <i class="fas fa-sync-alt"></i> Sync Now
                </button>
            </div>
        </div>
        
        <!-- Financial Sync Status for Treasurers -->
        {% if current_user_role == 'treasurer' %}
        <hr>
        <div class="row text-center">
            <div class="col-4">
                <div class="metric">
                    <h6 class="text-success">156</h6>
                    <small class="text-muted">Synced Transactions</small>
                </div>
            </div>
            <div class="col-4">
                <div class="metric">
                    <h6 class="text-info">KES 245,000</h6>
                    <small class="text-muted">Total Synced</small>
                </div>
            </div>
            <div class="col-4">
                <div class="metric">
                    <h6 class="text-warning">3</h6>
                    <small class="text-muted">Pending Items</small>
                </div>
            </div>
        </div>
        {% endif %}
    </div>
</div>
{% endif %}
```

## 📋 **IMPLEMENTATION STEPS**

### **Step 1: Update Environment Variables (Your Part)**
```env
QUICKBOOKS_CLIENT_ID=your_actual_client_id_from_intuit
QUICKBOOKS_CLIENT_SECRET=your_actual_client_secret_from_intuit
QUICKBOOKS_REDIRECT_URI=http://localhost:5000/integrations/accounting/quickbooks/callback
QUICKBOOKS_ENVIRONMENT=sandbox
```

### **Step 2: Role-Based Integration Routes (Enhancement Needed)**
- Create role-based decorators
- Update integration routes with proper access controls
- Add treasurer-specific QuickBooks endpoints

### **Step 3: UI Updates by Role (Enhancement Needed)**
- Add QuickBooks status to treasurer dashboard
- Hide QuickBooks features from secretaries and members
- Show role-appropriate actions and information

### **Step 4: Notification System (Enhancement Needed)**
- Notify treasurers of sync successes/failures
- Alert creators of connection issues
- Send financial sync reports to relevant roles

## 🔍 **CURRENT LIMITATIONS**

### **What Works Now:**
- ✅ Full QuickBooks integration implemented
- ✅ OAuth connection and sync functionality
- ✅ Admin-level access control
- ✅ Complete financial data synchronization

### **What Needs Enhancement:**
- ❌ Role-based access for treasurers
- ❌ Treasurer-specific dashboard features
- ❌ Role-appropriate UI customization
- ❌ Granular permission controls

## 🎯 **RECOMMENDED WORKFLOW**

### **For Chama Setup:**
1. **Creator** connects QuickBooks (admin-level access)
2. **Creator** configures sync settings and permissions
3. **Treasurer** gets access to sync financial data
4. **All roles** see appropriate status information

### **For Daily Operations:**
1. **Treasurer** syncs daily financial transactions
2. **Creator** monitors overall integration health
3. **Secretary** sees basic connection status
4. **Members** interact normally (no QuickBooks visibility)

### **For Financial Management:**
1. **Treasurer** ensures all transactions are synced
2. **Creator** reviews QuickBooks reports
3. **Treasurer** handles any sync errors or issues
4. **Creator** manages connection and settings

## ⚡ **QUICK ANSWER TO YOUR QUESTIONS:**

### **Q: Can treasurer and secretary see QuickBooks?**
**A: Currently NO** - Only system admins and creators can access QuickBooks features.

### **Q: Where will QuickBooks be seen?**
**A: Currently** in `/integrations` dashboard, but only for admins.

### **Q: Should treasurers have QuickBooks access?**
**A: YES** - They should be able to sync financial data and see sync status.

### **Q: How to implement this?**
**A: Follow the implementation steps above** to add role-based access control.

---

**Next Steps**: Would you like me to implement the role-based access control so treasurers can access QuickBooks financial sync features? 🎯
