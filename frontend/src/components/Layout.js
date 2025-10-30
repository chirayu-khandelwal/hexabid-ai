import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Users, BarChart3, MessageSquare, LogOut, Building2, Bell, HelpCircle, FolderOpen, TrendingUp, CreditCard, Shield, FileEdit } from 'lucide-react';

const Layout = ({ children, user, onLogout }) => {
  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/tenders', icon: FileText, label: 'Tenders' },
    { to: '/analytics', icon: TrendingUp, label: 'Analytics' },
    { to: '/document-preparation', icon: FileEdit, label: 'Doc Preparation' },
    { to: '/crm', icon: Users, label: 'CRM' },
    { to: '/reports', icon: BarChart3, label: 'Reports' },
    { to: '/documents', icon: FolderOpen, label: 'Documents' },
    { to: '/chat', icon: MessageSquare, label: 'Ask Hexa' },
    { to: '/notifications', icon: Bell, label: 'Notifications' },
    { to: '/support', icon: HelpCircle, label: 'Support' },
    { to: '/subscription', icon: CreditCard, label: 'Subscription' },
  ];

  // Add admin link if user is super admin
  if (user?.role === 'super_admin') {
    navItems.push({ to: '/admin', icon: Shield, label: 'Admin Panel' });
  }

  return (
    <div className="flex h-screen bg-slate-50" data-testid="layout">
      <aside className="w-64 sidebar flex flex-col overflow-y-auto" data-testid="sidebar">
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">HexaBid ERP</h1>
              <p className="text-xs text-slate-400">v3.0</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 py-6" data-testid="nav-menu">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `sidebar-link flex items-center gap-3 ${isActive ? 'active' : ''}`
              }
              data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-6 border-t border-slate-700">
          <div className="mb-4">
            <p className="text-sm text-slate-400">Logged in as</p>
            <p className="text-white font-medium" data-testid="user-name">{user?.full_name}</p>
            <p className="text-xs text-slate-400" data-testid="user-email">{user?.email}</p>
            {user?.role && (
              <span className="inline-block mt-2 px-2 py-1 bg-blue-600 text-white text-xs rounded">
                {user.role.replace('_', ' ')}
              </span>
            )}
          </div>
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-3 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition"
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto" data-testid="main-content">
        {children}
      </main>
    </div>
  );
};

export default Layout;
