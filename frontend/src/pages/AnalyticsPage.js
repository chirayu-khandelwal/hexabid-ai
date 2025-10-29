import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API, AuthContext } from '../App';
import Layout from '../components/Layout';
import { toast } from 'sonner';
import { TrendingUp, PieChart, BarChart3, Activity } from 'lucide-react';

const AnalyticsPage = () => {
  const { user, logout } = useContext(AuthContext);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/analytics/tender-trends`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrends(response.data);
    } catch (error) {
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <Layout user={user} onLogout={logout}>
      <div className="p-8" data-testid="analytics-page">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Advanced Analytics</h1>
          <p className="text-slate-600 mt-1">Deep insights into tender trends and performance</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="loader"></div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <div className="flex items-center gap-3 mb-6">
                  <PieChart className="w-6 h-6 text-blue-600" />
                  <h2 className="text-xl font-semibold text-slate-900">Tenders by Category</h2>
                </div>
                <div className="space-y-4">
                  {trends?.categories?.map((cat, idx) => (
                    <div key={idx}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-slate-700">{cat.name}</span>
                        <span className="text-sm text-slate-600">{cat.count} tenders</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-3">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full"
                          style={{ width: `${(cat.count / 45) * 100}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        Value: {formatCurrency(cat.value)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <div className="flex items-center gap-3 mb-6">
                  <BarChart3 className="w-6 h-6 text-green-600" />
                  <h2 className="text-xl font-semibold text-slate-900">Win Rate by Category</h2>
                </div>
                <div className="space-y-4">
                  {trends?.win_rate_by_category?.map((cat, idx) => (
                    <div key={idx}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-slate-700">{cat.category}</span>
                        <span className="text-sm font-bold text-green-600">{cat.win_rate}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-3">
                        <div
                          className="bg-gradient-to-r from-green-500 to-emerald-500 h-3 rounded-full"
                          style={{ width: `${cat.win_rate}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <div className="flex items-center gap-3 mb-6">
                <TrendingUp className="w-6 h-6 text-purple-600" />
                <h2 className="text-xl font-semibold text-slate-900">Monthly Trend Analysis</h2>
              </div>
              <div className="grid grid-cols-3 gap-4">
                {trends?.monthly_trend?.map((month, idx) => (
                  <div key={idx} className="p-4 border border-slate-200 rounded-lg">
                    <p className="text-sm text-slate-600 mb-2">{month.month} 2025</p>
                    <p className="text-2xl font-bold text-slate-900">{month.tenders}</p>
                    <p className="text-xs text-slate-500">tenders</p>
                    <p className="text-sm font-semibold text-purple-600 mt-2">
                      {formatCurrency(month.value)}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl p-6 text-white">
              <div className="flex items-center gap-3 mb-4">
                <Activity className="w-6 h-6" />
                <h2 className="text-xl font-semibold">Performance Summary</h2>
              </div>
              <div className="grid grid-cols-3 gap-6">
                <div>
                  <p className="text-blue-100 text-sm mb-1">Total Tender Value</p>
                  <p className="text-3xl font-bold">₹65Cr</p>
                </div>
                <div>
                  <p className="text-blue-100 text-sm mb-1">Average Win Rate</p>
                  <p className="text-3xl font-bold">65%</p>
                </div>
                <div>
                  <p className="text-blue-100 text-sm mb-1">Active Categories</p>
                  <p className="text-3xl font-bold">5</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default AnalyticsPage;
