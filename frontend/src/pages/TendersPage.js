import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API, AuthContext } from '../App';
import Layout from '../components/Layout';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, MapPin, Calendar, DollarSign } from 'lucide-react';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';

const TendersPage = () => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    fetchTenders();
  }, [selectedCategory]);

  const fetchTenders = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = selectedCategory ? `?category=${selectedCategory}` : '';
      const response = await axios.get(`${API}/tenders${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTenders(response.data);
    } catch (error) {
      toast.error('Failed to load tenders');
    } finally {
      setLoading(false);
    }
  };

  const filteredTenders = tenders.filter(tender =>
    tender.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tender.organization.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getDaysLeft = (deadline) => {
    const days = Math.ceil((new Date(deadline) - new Date()) / (1000 * 60 * 60 * 24));
    return days;
  };

  const categories = ['IT Services', 'Construction', 'Medical Equipment', 'Office Supplies', 'Consulting'];

  return (
    <Layout user={user} onLogout={logout}>
      <div className="p-8" data-testid="tenders-page">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2" data-testid="tenders-title">Available Tenders</h1>
          <p className="text-slate-600">Browse and analyze government and private sector tenders</p>
        </div>

        <div className="mb-6 flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
            <Input
              placeholder="Search tenders by title or organization..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 input-modern"
              data-testid="search-tenders-input"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 border border-slate-300 rounded-lg input-modern"
              data-testid="category-filter"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="loader"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4" data-testid="tenders-list">
            {filteredTenders.length === 0 ? (
              <div className="text-center py-20" data-testid="no-tenders">
                <p className="text-slate-500 mb-4">No tenders found</p>
                <p className="text-sm text-slate-400">Try importing tenders from the dashboard</p>
              </div>
            ) : (
              filteredTenders.map((tender) => {
                const daysLeft = getDaysLeft(tender.submission_deadline);
                return (
                  <div
                    key={tender.id}
                    className="tender-card animate-fade-in"
                    onClick={() => navigate(`/tenders/${tender.id}`)}
                    data-testid={`tender-card-${tender.id}`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="badge badge-info" data-testid="tender-source">{tender.source}</span>
                          <span className="badge badge-success" data-testid="tender-category">{tender.category}</span>
                        </div>
                        <h3 className="text-lg font-semibold text-slate-900 mb-1" data-testid="tender-title">
                          {tender.title}
                        </h3>
                        <p className="text-sm text-slate-600" data-testid="tender-organization">{tender.organization}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-slate-700">Tender ID</p>
                        <p className="text-xs text-slate-500" data-testid="tender-id">{tender.tender_id}</p>
                      </div>
                    </div>

                    <p className="text-sm text-slate-600 mb-4 line-clamp-2" data-testid="tender-description">
                      {tender.description}
                    </p>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-slate-100">
                      <div>
                        <div className="flex items-center gap-1 text-slate-500 mb-1">
                          <DollarSign className="w-4 h-4" />
                          <span className="text-xs">Estimated Value</span>
                        </div>
                        <p className="font-semibold text-slate-900" data-testid="tender-value">
                          {formatCurrency(tender.estimated_value)}
                        </p>
                      </div>
                      <div>
                        <div className="flex items-center gap-1 text-slate-500 mb-1">
                          <DollarSign className="w-4 h-4" />
                          <span className="text-xs">EMD Amount</span>
                        </div>
                        <p className="font-semibold text-slate-900" data-testid="tender-emd">
                          {formatCurrency(tender.emd_amount)}
                        </p>
                      </div>
                      <div>
                        <div className="flex items-center gap-1 text-slate-500 mb-1">
                          <MapPin className="w-4 h-4" />
                          <span className="text-xs">Location</span>
                        </div>
                        <p className="font-semibold text-slate-900" data-testid="tender-location">{tender.location}</p>
                      </div>
                      <div>
                        <div className="flex items-center gap-1 text-slate-500 mb-1">
                          <Calendar className="w-4 h-4" />
                          <span className="text-xs">Deadline</span>
                        </div>
                        <p className="font-semibold text-slate-900" data-testid="tender-deadline">
                          {formatDate(tender.submission_deadline)}
                        </p>
                        <p className={`text-xs mt-1 ${
                          daysLeft <= 5 ? 'text-red-600' : daysLeft <= 15 ? 'text-amber-600' : 'text-green-600'
                        }`}>
                          {daysLeft > 0 ? `${daysLeft} days left` : 'Expired'}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default TendersPage;
