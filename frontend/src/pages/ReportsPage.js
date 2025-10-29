import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API, AuthContext } from '../App';
import Layout from '../components/Layout';
import { toast } from 'sonner';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

const ReportsPage = () => {
  const { user, logout } = useContext(AuthContext);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReport();
  }, []);

  const fetchReport = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/reports/win-loss`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setReport(response.data);
    } catch (error) {
      toast.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout user={user} onLogout={logout}>
      <div className="p-8" data-testid="reports-page">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900" data-testid="reports-title">Reports & Analytics</h1>
          <p className="text-slate-600 mt-1">Track your bidding performance and insights</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="loader"></div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200" data-testid="total-bids-card">
                <div className="flex items-center justify-between mb-2">
                  <BarChart3 className="w-8 h-8 text-blue-600" />
                  <span className="text-xs text-slate-500">Total</span>
                </div>
                <h3 className="text-3xl font-bold text-slate-900">{report?.total_bids || 0}</h3>
                <p className="text-sm text-slate-600">Total Bids</p>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200" data-testid="wins-card">
                <div className="flex items-center justify-between mb-2">
                  <TrendingUp className="w-8 h-8 text-green-600" />
                  <span className="text-xs text-green-600 font-semibold">↑ Wins</span>
                </div>
                <h3 className="text-3xl font-bold text-slate-900">{report?.wins || 0}</h3>
                <p className="text-sm text-slate-600">Won Bids</p>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200" data-testid="losses-card">
                <div className="flex items-center justify-between mb-2">
                  <TrendingDown className="w-8 h-8 text-red-600" />
                  <span className="text-xs text-red-600 font-semibold">↓ Losses</span>
                </div>
                <h3 className="text-3xl font-bold text-slate-900">{report?.losses || 0}</h3>
                <p className="text-sm text-slate-600">Lost Bids</p>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200" data-testid="win-rate-card">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl">🎯</span>
                  <span className="text-xs text-purple-600 font-semibold">Rate</span>
                </div>
                <h3 className="text-3xl font-bold text-slate-900">{report?.win_rate || 0}%</h3>
                <p className="text-sm text-slate-600">Win Rate</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200" data-testid="monthly-performance">
                <h2 className="text-xl font-semibold text-slate-900 mb-6">Monthly Performance</h2>
                <div className="space-y-4">
                  {report?.monthly_data?.map((month) => (
                    <div key={month.month} className="flex items-center gap-4">
                      <div className="w-16 text-sm font-medium text-slate-600">{month.month}</div>
                      <div className="flex-1">
                        <div className="flex gap-2 h-8">
                          <div
                            className="bg-green-500 rounded flex items-center justify-center text-white text-xs font-semibold"
                            style={{ width: `${(month.wins / (month.wins + month.losses)) * 100}%` }}
                          >
                            {month.wins > 0 && month.wins}
                          </div>
                          <div
                            className="bg-red-500 rounded flex items-center justify-center text-white text-xs font-semibold"
                            style={{ width: `${(month.losses / (month.wins + month.losses)) * 100}%` }}
                          >
                            {month.losses > 0 && month.losses}
                          </div>
                        </div>
                      </div>
                      <div className="w-20 text-right text-sm text-slate-600">
                        {month.wins + month.losses} bids
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex gap-6 mt-6 pt-6 border-t border-slate-200">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-green-500 rounded"></div>
                    <span className="text-sm text-slate-600">Wins</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-red-500 rounded"></div>
                    <span className="text-sm text-slate-600">Losses</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200" data-testid="insights">
                <h2 className="text-xl font-semibold text-slate-900 mb-6">Key Insights</h2>
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <TrendingUp className="w-4 h-4 text-green-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900 mb-1">Strong Performance</h3>
                        <p className="text-sm text-slate-600">
                          Your win rate is {report?.win_rate}%, which is above industry average.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <BarChart3 className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900 mb-1">Active Bidding</h3>
                        <p className="text-sm text-slate-600">
                          You have {report?.pending || 0} pending bids awaiting results.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-purple-50 rounded-lg">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-purple-600 font-semibold text-sm">🎯</span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900 mb-1">Focus Areas</h3>
                        <p className="text-sm text-slate-600">
                          IT Services and Construction categories show highest success rates.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
};

export default ReportsPage;
