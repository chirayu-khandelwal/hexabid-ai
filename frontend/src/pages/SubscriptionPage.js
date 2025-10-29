import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API, AuthContext } from '../App';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import { CreditCard, Calendar, Zap, CheckCircle } from 'lucide-react';

const SubscriptionPage = () => {
  const { user, logout } = useContext(AuthContext);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubscription();
  }, []);

  const fetchSubscription = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/subscription/my-subscription`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSubscription(response.data);
    } catch (error) {
      toast.error('Failed to load subscription');
    } finally {
      setLoading(false);
    }
  };

  const plans = [
    {
      name: 'Starter',
      price: 999,
      credits: 200,
      features: ['Basic modules', '200 AI credits', 'Email support', 'Basic reports']
    },
    {
      name: 'Professional',
      price: 2999,
      credits: 1000,
      features: ['All modules', '1000 AI credits', 'Priority support', 'Advanced analytics', 'Competitor analysis']
    },
    {
      name: 'Enterprise',
      price: 4999,
      credits: 3000,
      features: ['Full access', '3000 AI credits', '24/7 support', 'Custom integrations', 'Dedicated manager']
    }
  ];

  return (
    <Layout user={user} onLogout={logout}>
      <div className="p-8" data-testid="subscription-page">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Subscription & Billing</h1>
          <p className="text-slate-600 mt-1">Manage your subscription plan and billing</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="loader"></div>
          </div>
        ) : (
          <div className="space-y-8">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm mb-1">Current Plan</p>
                  <h2 className="text-3xl font-bold capitalize">{subscription?.plan || 'Professional'}</h2>
                  <p className="text-blue-100 mt-2">Valid until {new Date(subscription?.end_date).toLocaleDateString()}</p>
                </div>
                <div className="text-right">
                  <p className="text-blue-100 text-sm mb-1">AI Credits Remaining</p>
                  <p className="text-4xl font-bold">{subscription?.ai_credits || 0}</p>
                </div>
              </div>
            </div>

            <div>
              <h2 className="text-2xl font-semibold text-slate-900 mb-6">Available Plans</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {plans.map((plan, idx) => (
                  <div
                    key={idx}
                    className={`bg-white rounded-xl p-6 border-2 ${
                      plan.name.toLowerCase() === subscription?.plan
                        ? 'border-blue-500 shadow-lg'
                        : 'border-slate-200'
                    } transition hover:shadow-lg`}
                  >
                    <div className="text-center mb-6">
                      <h3 className="text-2xl font-bold text-slate-900 mb-2">{plan.name}</h3>
                      <div className="flex items-baseline justify-center gap-1">
                        <span className="text-4xl font-bold text-slate-900">₹{plan.price}</span>
                        <span className="text-slate-600">/month</span>
                      </div>
                      <p className="text-sm text-slate-600 mt-2">{plan.credits} AI credits</p>
                    </div>

                    <ul className="space-y-3 mb-6">
                      {plan.features.map((feature, fidx) => (
                        <li key={fidx} className="flex items-start gap-2">
                          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                          <span className="text-sm text-slate-600">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <Button
                      className={`w-full ${
                        plan.name.toLowerCase() === subscription?.plan
                          ? 'bg-slate-300 text-slate-600 cursor-not-allowed'
                          : 'btn-primary'
                      }`}
                      disabled={plan.name.toLowerCase() === subscription?.plan}
                    >
                      {plan.name.toLowerCase() === subscription?.plan ? 'Current Plan' : 'Upgrade'}
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h2 className="text-xl font-semibold text-slate-900 mb-4">Payment Method</h2>
              <div className="flex items-center gap-4 p-4 border border-slate-200 rounded-lg">
                <CreditCard className="w-8 h-8 text-slate-400" />
                <div className="flex-1">
                  <p className="font-medium text-slate-900">•••• •••• •••• 4242</p>
                  <p className="text-sm text-slate-600">Expires 12/2026</p>
                </div>
                <Button variant="outline">Update</Button>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h2 className="text-xl font-semibold text-slate-900 mb-4">Billing History</h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 border border-slate-100 rounded-lg">
                  <div>
                    <p className="font-medium text-slate-900">Professional Plan</p>
                    <p className="text-sm text-slate-600">Jan 1, 2025</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-slate-900">₹2,999</p>
                    <span className="text-xs text-green-600">Paid</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default SubscriptionPage;
