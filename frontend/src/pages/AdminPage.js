import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API, AuthContext } from '../App';
import Layout from '../components/Layout';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { Users, FileText, BarChart3, DollarSign, Shield } from 'lucide-react';

const AdminPage = () => {
  const { user, logout } = useContext(AuthContext);
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.role !== 'super_admin') {
      toast.error('Admin access required');
      return;
    }
    fetchAdminData();
  }, [user]);

  const fetchAdminData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      const [statsRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/stats`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/users`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setStats(statsRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  if (user?.role !== 'super_admin') {
    return (
      <Layout user={user} onLogout={logout}>
        <div className="p-8 text-center py-20">
          <Shield className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Access Denied</h2>
          <p className="text-slate-600">You don't have permission to access the admin panel</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={logout}>
      <div className="p-8" data-testid="admin-page">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Admin Panel</h1>
          <p className="text-slate-600 mt-1">System administration and management</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="loader"></div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="stat-card">
                <div className="flex items-center justify-between mb-4">
                  <Users className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-3xl font-bold text-slate-900">{stats?.total_users || 0}</h3>
                <p className="text-sm text-slate-600">Total Users</p>
              </div>

              <div className="stat-card">
                <div className="flex items-center justify-between mb-4">
                  <FileText className="w-8 h-8 text-purple-600" />
                </div>
                <h3 className="text-3xl font-bold text-slate-900">{stats?.total_tenders || 0}</h3>
                <p className="text-sm text-slate-600">Total Tenders</p>
              </div>

              <div className="stat-card">
                <div className="flex items-center justify-between mb-4">
                  <BarChart3 className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-3xl font-bold text-slate-900">{stats?.total_analyses || 0}</h3>
                <p className="text-sm text-slate-600">AI Analyses</p>
              </div>

              <div className="stat-card">
                <div className="flex items-center justify-between mb-4">
                  <DollarSign className="w-8 h-8 text-amber-600" />
                </div>
                <h3 className="text-3xl font-bold text-slate-900">
                  ₹{((stats?.revenue_this_month || 0) / 100000).toFixed(1)}L
                </h3>
                <p className="text-sm text-slate-600">Revenue (Month)</p>
              </div>
            </div>

            <Tabs defaultValue="users" className="w-full">
              <TabsList>
                <TabsTrigger value="users">Users Management</TabsTrigger>
                <TabsTrigger value="system">System Info</TabsTrigger>
              </TabsList>

              <TabsContent value="users">
                <div className="bg-white rounded-xl p-6 border border-slate-200">
                  <h2 className="text-xl font-semibold text-slate-900 mb-4">Registered Users</h2>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-200">
                          <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">Name</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">Email</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">Role</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">Company</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((u) => (
                          <tr key={u.id} className="border-b border-slate-100 hover:bg-slate-50">
                            <td className="py-3 px-4 text-sm text-slate-900">{u.full_name}</td>
                            <td className="py-3 px-4 text-sm text-slate-600">{u.email}</td>
                            <td className="py-3 px-4">
                              <span className="badge badge-info">{u.role}</span>
                            </td>
                            <td className="py-3 px-4 text-sm text-slate-600">{u.company_name || '-'}</td>
                            <td className="py-3 px-4">
                              <span className={`badge ${u.is_active ? 'badge-success' : 'badge-danger'}`}>
                                {u.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="system">
                <div className="bg-white rounded-xl p-6 border border-slate-200">
                  <h2 className="text-xl font-semibold text-slate-900 mb-4">System Information</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-600">Active Subscriptions</p>
                      <p className="text-2xl font-bold text-slate-900">{stats?.active_subscriptions || 0}</p>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-600">Support Tickets</p>
                      <p className="text-2xl font-bold text-slate-900">{stats?.total_support_tickets || 0}</p>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-600">System Status</p>
                      <p className="text-lg font-semibold text-green-600">Healthy</p>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-600">Version</p>
                      <p className="text-lg font-semibold text-slate-900">v3.0</p>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </Layout>
  );
};

export default AdminPage;
