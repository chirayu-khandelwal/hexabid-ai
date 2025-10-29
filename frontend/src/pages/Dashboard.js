import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API, AuthContext } from '../App';
import Layout from '../components/Layout';
import { TrendingUp, FileText, Target, DollarSign, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

const Dashboard = () => {
  const { user, logout } = useContext(AuthContext);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/dashboard/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to load dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  const handleImportTenders = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/tenders/import`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(response.data.message);
      fetchStats();
    } catch (error) {
      toast.error('Failed to import tenders');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout user={user} onLogout={logout}>
      <div className="p-8" data-testid="dashboard-page">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900" data-testid="dashboard-title">
              Welcome back, {user?.full_name}!
            </h1>
            <p className="text-slate-600 mt-1">Here's your tender management overview</p>
          </div>
          <button
            onClick={handleImportTenders}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            data-testid="import-tenders-btn"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Import Tenders
          </button>
        </div>

        {loading && !stats ? (
          <div className="flex justify-center py-20">
            <div className="loader"></div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="stat-card card-hover" data-testid="stat-total-tenders">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-6 h-6 text-blue-600" />
                  </div>
                  <span className="text-xs text-green-600 font-semibold">Active</span>
                </div>
                <h3 className="text-2xl font-bold text-slate-900">{stats?.total_tenders || 0}</h3>
                <p className="text-slate-600 text-sm">Total Tenders</p>
              </div>

              <div className="stat-card card-hover" data-testid="stat-my-bids">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Target className="w-6 h-6 text-purple-600" />
                  </div>
                  <span className="text-xs text-purple-600 font-semibold">This Month</span>
                </div>
                <h3 className="text-2xl font-bold text-slate-900">{stats?.my_bids || 0}</h3>
                <p className="text-slate-600 text-sm">My Bids</p>
              </div>

              <div className="stat-card card-hover" data-testid="stat-win-rate">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-green-600" />
                  </div>
                  <span className="text-xs text-green-600 font-semibold">↑ +5%</span>
                </div>
                <h3 className="text-2xl font-bold text-slate-900">{stats?.win_rate || 0}%</h3>
                <p className="text-slate-600 text-sm">Win Rate</p>
              </div>

              <div className="stat-card card-hover" data-testid="stat-estimated-value">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-amber-600" />
                  </div>
                  <span className="text-xs text-amber-600 font-semibold">Estimated</span>
                </div>
                <h3 className="text-2xl font-bold text-slate-900">
                  ₹{((stats?.estimated_value || 0) / 10000000).toFixed(1)}Cr
                </h3>
                <p className="text-slate-600 text-sm">Total Value</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200" data-testid="recent-activity">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Recent Activity</h2>
                <div className="space-y-4">
                  <div className="flex items-start gap-3 pb-3 border-b border-slate-100">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <FileText className="w-4 h-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">New tender imported</p>
                      <p className="text-xs text-slate-500">Supply and Installation of IT Services</p>
                      <p className="text-xs text-slate-400 mt-1">2 hours ago</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 pb-3 border-b border-slate-100">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Target className="w-4 h-4 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">Analysis completed</p>
                      <p className="text-xs text-slate-500">Medical Equipment tender analyzed</p>
                      <p className="text-xs text-slate-400 mt-1">5 hours ago</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <TrendingUp className="w-4 h-4 text-purple-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">Win probability calculated</p>
                      <p className="text-xs text-slate-500">Office Supplies - 68% win chance</p>
                      <p className="text-xs text-slate-400 mt-1">1 day ago</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200" data-testid="quick-actions">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h2>
                <div className="grid grid-cols-2 gap-3">
                  <a
                    href="/tenders"
                    className="p-4 border-2 border-slate-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition text-center"
                    data-testid="quick-action-browse-tenders"
                  >
                    <FileText className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                    <p className="text-sm font-medium text-slate-900">Browse Tenders</p>
                  </a>
                  <a
                    href="/chat"
                    className="p-4 border-2 border-slate-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition text-center"
                    data-testid="quick-action-ask-hexa"
                  >
                    <svg className="w-6 h-6 text-purple-600 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    <p className="text-sm font-medium text-slate-900">Ask Hexa AI</p>
                  </a>
                  <a
                    href="/crm"
                    className="p-4 border-2 border-slate-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition text-center"
                    data-testid="quick-action-manage-contacts"
                  >
                    <svg className="w-6 h-6 text-green-600 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    <p className="text-sm font-medium text-slate-900">Manage Contacts</p>
                  </a>
                  <a
                    href="/reports"
                    className="p-4 border-2 border-slate-200 rounded-lg hover:border-amber-500 hover:bg-amber-50 transition text-center"
                    data-testid="quick-action-view-reports"
                  >
                    <svg className="w-6 h-6 text-amber-600 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <p className="text-sm font-medium text-slate-900">View Reports</p>
                  </a>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
};

export default Dashboard;
