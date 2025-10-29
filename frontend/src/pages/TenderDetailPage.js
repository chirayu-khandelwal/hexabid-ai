import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API, AuthContext } from '../App';
import Layout from '../components/Layout';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { ArrowLeft, TrendingUp, Users, FileText, Calculator } from 'lucide-react';

const TenderDetailPage = () => {
  const { user, logout } = useContext(AuthContext);
  const { tenderId } = useParams();
  const navigate = useNavigate();
  const [tender, setTender] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [competitors, setCompetitors] = useState(null);
  const [winPrediction, setWinPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    fetchTenderDetails();
  }, [tenderId]);

  const fetchTenderDetails = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/tenders/${tenderId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTender(response.data);
      
      // Try to fetch existing analysis
      try {
        const analysisRes = await axios.get(`${API}/tenders/${tenderId}/analysis`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setAnalysis(analysisRes.data);
      } catch (err) {
        // Analysis doesn't exist yet
      }
    } catch (error) {
      toast.error('Failed to load tender details');
      navigate('/tenders');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeTender = async () => {
    setAnalyzing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/tenders/${tenderId}/analyze`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalysis(response.data);
      toast.success('Analysis completed!');
    } catch (error) {
      toast.error('Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAnalyzeCompetitors = async () => {
    setAnalyzing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/tenders/${tenderId}/competitors`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCompetitors(response.data);
      toast.success('Competitor analysis completed!');
    } catch (error) {
      toast.error('Competitor analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleWinPrediction = async () => {
    setAnalyzing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/tenders/${tenderId}/win-prediction`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setWinPrediction(response.data);
      toast.success('Win probability calculated!');
    } catch (error) {
      toast.error('Prediction failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={logout}>
        <div className="flex justify-center py-20">
          <div className="loader"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={logout}>
      <div className="p-8" data-testid="tender-detail-page">
        <button
          onClick={() => navigate('/tenders')}
          className="flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-6 transition"
          data-testid="back-to-tenders-btn"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Tenders
        </button>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 mb-6" data-testid="tender-header">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="badge badge-info">{tender.source}</span>
                <span className="badge badge-success">{tender.category}</span>
                <span className="badge badge-warning">{tender.status}</span>
              </div>
              <h1 className="text-3xl font-bold text-slate-900 mb-2" data-testid="tender-detail-title">{tender.title}</h1>
              <p className="text-slate-600">{tender.organization}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-500">Tender ID</p>
              <p className="font-semibold text-slate-900" data-testid="tender-detail-id">{tender.tender_id}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-slate-200">
            <div>
              <p className="text-sm text-slate-500 mb-1">Estimated Value</p>
              <p className="text-xl font-bold text-slate-900">{formatCurrency(tender.estimated_value)}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500 mb-1">EMD Amount</p>
              <p className="text-xl font-bold text-slate-900">{formatCurrency(tender.emd_amount)}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500 mb-1">Published Date</p>
              <p className="text-lg font-semibold text-slate-900">{formatDate(tender.published_date)}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500 mb-1">Submission Deadline</p>
              <p className="text-lg font-semibold text-red-600">{formatDate(tender.submission_deadline)}</p>
            </div>
          </div>
        </div>

        <Tabs defaultValue="details" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="details" data-testid="tab-details">Details</TabsTrigger>
            <TabsTrigger value="analysis" data-testid="tab-analysis">AI Analysis</TabsTrigger>
            <TabsTrigger value="competitors" data-testid="tab-competitors">Competitors</TabsTrigger>
            <TabsTrigger value="prediction" data-testid="tab-prediction">Win Prediction</TabsTrigger>
          </TabsList>

          <TabsContent value="details" data-testid="content-details">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h2 className="text-xl font-semibold text-slate-900 mb-4">Description</h2>
              <p className="text-slate-600 mb-6">{tender.description}</p>

              <h3 className="text-lg font-semibold text-slate-900 mb-3">Eligibility Criteria</h3>
              <ul className="list-disc list-inside space-y-2 mb-6">
                {tender.eligibility_criteria.map((criteria, idx) => (
                  <li key={idx} className="text-slate-600">{criteria}</li>
                ))}
              </ul>

              <h3 className="text-lg font-semibold text-slate-900 mb-3">Technical Specifications</h3>
              <div className="bg-slate-50 rounded-lg p-4">
                {Object.entries(tender.technical_specs).map(([key, value]) => (
                  <div key={key} className="flex justify-between py-2 border-b border-slate-200 last:border-0">
                    <span className="text-slate-600 capitalize">{key.replace('_', ' ')}</span>
                    <span className="font-medium text-slate-900">{value}</span>
                  </div>
                ))}
              </div>

              <div className="mt-6">
                <p className="text-sm text-slate-500">Location: <span className="font-semibold text-slate-900">{tender.location}</span></p>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="analysis" data-testid="content-analysis">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              {!analysis ? (
                <div className="text-center py-12">
                  <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-600 mb-4">No analysis available yet</p>
                  <Button
                    onClick={handleAnalyzeTender}
                    disabled={analyzing}
                    className="btn-primary"
                    data-testid="analyze-tender-btn"
                  >
                    {analyzing ? 'Analyzing...' : 'Analyze Tender with AI'}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-3">AI Summary</h3>
                    <p className="text-slate-600 bg-blue-50 p-4 rounded-lg">{analysis.ai_summary}</p>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-3">Key Requirements</h3>
                    <ul className="space-y-2">
                      {analysis.key_requirements.map((req, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-sm flex-shrink-0 mt-0.5">✓</span>
                          <span className="text-slate-600">{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-3">Potential Risks</h3>
                    <ul className="space-y-2">
                      {analysis.risks.map((risk, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center text-red-600 text-sm flex-shrink-0 mt-0.5">⚠</span>
                          <span className="text-slate-600">{risk}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-3">Opportunities</h3>
                    <ul className="space-y-2">
                      {analysis.opportunities.map((opp, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center text-green-600 text-sm flex-shrink-0 mt-0.5">★</span>
                          <span className="text-slate-600">{opp}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                    <div>
                      <p className="text-sm text-slate-500">Estimated Effort</p>
                      <p className="text-lg font-semibold text-slate-900">{analysis.estimated_effort}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="competitors" data-testid="content-competitors">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              {!competitors ? (
                <div className="text-center py-12">
                  <Users className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-600 mb-4">No competitor analysis available yet</p>
                  <Button
                    onClick={handleAnalyzeCompetitors}
                    disabled={analyzing}
                    className="btn-primary"
                    data-testid="analyze-competitors-btn"
                  >
                    {analyzing ? 'Analyzing...' : 'Analyze Competitors'}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-3">Market Analysis</h3>
                    <p className="text-slate-600 bg-purple-50 p-4 rounded-lg">{competitors.market_analysis}</p>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">Competitor Overview</h3>
                    <div className="space-y-3">
                      {competitors.competitors.map((comp, idx) => (
                        <div key={idx} className="p-4 border border-slate-200 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-slate-900">{comp.name}</h4>
                            <span className={`badge ${comp.threat === 'high' ? 'badge-danger' : comp.threat === 'medium' ? 'badge-warning' : 'badge-success'}`}>
                              {comp.threat} threat
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <p className="text-slate-500">Win Rate</p>
                              <p className="font-semibold text-slate-900">{comp.win_rate}%</p>
                            </div>
                            <div>
                              <p className="text-slate-500">Past Bids</p>
                              <p className="font-semibold text-slate-900">{comp.past_bids}</p>
                            </div>
                            <div>
                              <p className="text-slate-500">Avg Margin</p>
                              <p className="font-semibold text-slate-900">{comp.avg_margin}%</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-3">Your Competitive Advantage</h3>
                    <ul className="space-y-2">
                      {competitors.competitive_advantage.map((adv, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center text-green-600 text-sm flex-shrink-0 mt-0.5">✓</span>
                          <span className="text-slate-600">{adv}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="pt-4 border-t border-slate-200">
                    <p className="text-sm text-slate-500">Overall Threat Level</p>
                    <p className="text-lg font-semibold text-slate-900">{competitors.threat_level}</p>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="prediction" data-testid="content-prediction">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              {!winPrediction ? (
                <div className="text-center py-12">
                  <TrendingUp className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-600 mb-4">No win prediction available yet</p>
                  <Button
                    onClick={handleWinPrediction}
                    disabled={analyzing}
                    className="btn-primary"
                    data-testid="predict-win-btn"
                  >
                    {analyzing ? 'Calculating...' : 'Calculate Win Probability'}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="text-center py-8">
                    <p className="text-sm text-slate-500 mb-2">Estimated Win Probability</p>
                    <div className="relative inline-block">
                      <svg className="w-32 h-32" viewBox="0 0 120 120">
                        <circle cx="60" cy="60" r="54" fill="none" stroke="#e2e8f0" strokeWidth="12" />
                        <circle
                          cx="60"
                          cy="60"
                          r="54"
                          fill="none"
                          stroke="#3b82f6"
                          strokeWidth="12"
                          strokeDasharray={`${2 * Math.PI * 54 * (winPrediction.win_probability / 100)}, ${2 * Math.PI * 54}`}
                          transform="rotate(-90 60 60)"
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-3xl font-bold text-slate-900">{winPrediction.win_probability}%</span>
                      </div>
                    </div>
                    <p className="text-sm text-slate-500 mt-4">
                      Confidence: <span className="font-semibold text-slate-900">{winPrediction.confidence_score}%</span>
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <Calculator className="w-8 h-8 text-blue-600 mb-2" />
                      <p className="text-sm text-slate-600 mb-1">Recommended Bid Margin</p>
                      <p className="text-2xl font-bold text-slate-900">{winPrediction.recommended_bid_margin}%</p>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg">
                      <TrendingUp className="w-8 h-8 text-green-600 mb-2" />
                      <p className="text-sm text-slate-600 mb-1">Win Probability</p>
                      <p className="text-2xl font-bold text-slate-900">
                        {winPrediction.win_probability >= 60 ? 'High' : winPrediction.win_probability >= 40 ? 'Medium' : 'Low'}
                      </p>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-3">Key Factors</h3>
                    <div className="grid grid-cols-2 gap-4">
                      {Object.entries(winPrediction.factors).map(([key, value]) => (
                        <div key={key} className="p-3 border border-slate-200 rounded-lg">
                          <p className="text-sm text-slate-500 capitalize">{key.replace('_', ' ')}</p>
                          <p className="font-semibold text-slate-900">{value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default TenderDetailPage;
