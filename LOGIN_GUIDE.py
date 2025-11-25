"""
Quick Login Guide for Cost Control Dashboard
"""

print("\n" + "="*70)
print("COST CONTROL DASHBOARD - LOGIN INFORMATION")
print("="*70)

print("\n📍 Access URL:")
print("   http://127.0.0.1:5000")
print("   or")
print("   http://127.0.0.1:5000/login")

print("\n👤 Cost Control User Credentials:")
print("   Email: kelvinibeh31101@gmail.com")
print("   Name: Hightower")
print("   Role: hq_cost_control")
print("   Password: [Use existing password]")

print("\n🎯 After Login:")
print("   You will be automatically redirected to:")
print("   http://127.0.0.1:5000/cost-control/manager/dashboard")

print("\n📊 Dashboard Features:")
print("   ✓ Real-time KPIs (Projects, Budgets, Spending)")
print("   ✓ Budget Alerts (84.1% usage warning)")
print("   ✓ Recent Cost Entries (24 transactions)")
print("   ✓ Pending Approvals (4 items)")
print("   ✓ Budget Adjustments (1 pending)")
print("   ✓ Interactive Charts (Spending by Category, Top Projects)")

print("\n💡 User Info Display:")
print("   ✓ User avatar with name initial")
print("   ✓ Full name in header: 'Hightower'")
print("   ✓ Notification badge: 5 (4 approvals + 1 adjustment)")
print("   ✓ Role-based sidebar navigation")

print("\n🔐 Security:")
print("   ✓ @role_required decorator protecting routes")
print("   ✓ Only HQ_COST_CONTROL and SUPER_HQ roles can access")
print("   ✓ Session-based authentication via Flask-Login")

print("\n" + "="*70)
print("✅ Dashboard is ready! Login with the credentials above.")
print("="*70 + "\n")
