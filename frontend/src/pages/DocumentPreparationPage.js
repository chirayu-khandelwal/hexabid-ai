import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API, AuthContext } from '../App';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { FileText, Download, Plus, Trash2, Calculator } from 'lucide-react';

const DocumentPreparationPage = () => {
  const { user, logout } = useContext(AuthContext);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTender, setSelectedTender] = useState(null);
  
  // BOQ states
  const [boqItems, setBOQItems] = useState([
    { description: '', unit: 'Nos', quantity: 1, rate: 0 }
  ]);
  
  // Company data states
  const [companyData, setCompanyData] = useState({
    name: '',
    established_year: '2020',
    gst_number: '',
    pan_number: '',
    address: '',
    phone: '',
    email: '',
    website: '',
    authorized_person: '',
    designation: 'Director'
  });
  
  // EMD Calculator
  const [tenderValue, setTenderValue] = useState('');
  const [emdPercentage, setEMDPercentage] = useState(2.0);
  const [emdResult, setEMDResult] = useState(null);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/documents/templates`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTemplates(response.data);
    } catch (error) {
      toast.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const addBOQItem = () => {
    setBOQItems([...boqItems, { description: '', unit: 'Nos', quantity: 1, rate: 0 }]);
  };

  const removeBOQItem = (index) => {
    setBOQItems(boqItems.filter((_, i) => i !== index));
  };

  const updateBOQItem = (index, field, value) => {
    const updated = [...boqItems];
    updated[index][field] = value;
    setBOQItems(updated);
  };

  const calculateBOQTotal = () => {
    return boqItems.reduce((total, item) => {
      return total + (parseFloat(item.quantity) || 0) * (parseFloat(item.rate) || 0);
    }, 0);
  };

  const generateBOQ = async () => {
    if (!selectedTender) {
      toast.error('Please select a tender first');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/documents/generate-boq`,
        { tender_id: selectedTender, items: boqItems },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(response.data.message);
    } catch (error) {
      toast.error('Failed to generate BOQ');
    }
  };

  const generateCoverLetter = async () => {
    if (!selectedTender) {
      toast.error('Please select a tender first');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/documents/generate-cover-letter`,
        { tender_id: selectedTender, company_data: companyData },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(response.data.message);
    } catch (error) {
      toast.error('Failed to generate cover letter');
    }
  };

  const generateCompanyProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/documents/generate-company-profile`,
        { company_data: companyData },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(response.data.message);
    } catch (error) {
      toast.error('Failed to generate company profile');
    }
  };

  const calculateEMD = async () => {
    if (!tenderValue) {
      toast.error('Please enter tender value');
      return;
    }

    try {
      const response = await axios.post(`${API}/documents/calculate-emd`, null, {
        params: { tender_value: tenderValue, emd_percentage: emdPercentage }
      });
      setEMDResult(response.data);
    } catch (error) {
      toast.error('Failed to calculate EMD');
    }
  };

  return (
    <Layout user={user} onLogout={logout}>
      <div className="p-8" data-testid="document-preparation-page">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Document Preparation</h1>
          <p className="text-slate-600 mt-1">Generate professional tender bidding documents</p>
        </div>

        <Tabs defaultValue="boq" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="boq">BOQ Generator</TabsTrigger>
            <TabsTrigger value="cover">Cover Letter</TabsTrigger>
            <TabsTrigger value="profile">Company Profile</TabsTrigger>
            <TabsTrigger value="calculator">EMD Calculator</TabsTrigger>
            <TabsTrigger value="templates">Templates</TabsTrigger>
          </TabsList>

          {/* BOQ Generator */}
          <TabsContent value="boq">
            <Card>
              <CardHeader>
                <CardTitle>Bill of Quantities (BOQ)</CardTitle>
                <CardDescription>Create detailed BOQ for your tender submission</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {boqItems.map((item, index) => (
                    <div key={index} className="grid grid-cols-12 gap-4 items-end p-4 border border-slate-200 rounded-lg">
                      <div className="col-span-5">
                        <Label>Description</Label>
                        <Input
                          placeholder="Item description"
                          value={item.description}
                          onChange={(e) => updateBOQItem(index, 'description', e.target.value)}
                        />
                      </div>
                      <div className="col-span-2">
                        <Label>Unit</Label>
                        <select
                          value={item.unit}
                          onChange={(e) => updateBOQItem(index, 'unit', e.target.value)}
                          className="w-full px-3 py-2 border border-slate-300 rounded-md"
                        >
                          <option>Nos</option>
                          <option>Set</option>
                          <option>Kg</option>
                          <option>Meter</option>
                          <option>Sq.m</option>
                          <option>Liter</option>
                        </select>
                      </div>
                      <div className="col-span-2">
                        <Label>Quantity</Label>
                        <Input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => updateBOQItem(index, 'quantity', e.target.value)}
                        />
                      </div>
                      <div className="col-span-2">
                        <Label>Rate (₹)</Label>
                        <Input
                          type="number"
                          value={item.rate}
                          onChange={(e) => updateBOQItem(index, 'rate', e.target.value)}
                        />
                      </div>
                      <div className="col-span-1">
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => removeBOQItem(index)}
                          disabled={boqItems.length === 1}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}

                  <Button onClick={addBOQItem} variant="outline" className="w-full">
                    <Plus className="w-4 h-4 mr-2" />
                    Add Item
                  </Button>

                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <div className="flex justify-between mb-2">
                      <span className="font-semibold">Subtotal:</span>
                      <span>₹{calculateBOQTotal().toLocaleString('en-IN')}</span>
                    </div>
                    <div className="flex justify-between mb-2">
                      <span className="font-semibold">GST @ 18%:</span>
                      <span>₹{(calculateBOQTotal() * 0.18).toLocaleString('en-IN')}</span>
                    </div>
                    <div className="flex justify-between text-lg font-bold border-t border-slate-300 pt-2">
                      <span>Grand Total:</span>
                      <span>₹{(calculateBOQTotal() * 1.18).toLocaleString('en-IN')}</span>
                    </div>
                  </div>

                  <Button onClick={generateBOQ} className="w-full btn-primary">
                    <Download className="w-4 h-4 mr-2" />
                    Generate BOQ Excel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Cover Letter */}
          <TabsContent value="cover">
            <Card>
              <CardHeader>
                <CardTitle>Cover Letter Generator</CardTitle>
                <CardDescription>Generate professional cover letter for tender submission</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Company Name *</Label>
                    <Input
                      value={companyData.name}
                      onChange={(e) => setCompanyData({ ...companyData, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Authorized Person *</Label>
                    <Input
                      value={companyData.authorized_person}
                      onChange={(e) => setCompanyData({ ...companyData, authorized_person: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Designation *</Label>
                    <Input
                      value={companyData.designation}
                      onChange={(e) => setCompanyData({ ...companyData, designation: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Phone Number *</Label>
                    <Input
                      value={companyData.phone}
                      onChange={(e) => setCompanyData({ ...companyData, phone: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Email *</Label>
                    <Input
                      type="email"
                      value={companyData.email}
                      onChange={(e) => setCompanyData({ ...companyData, email: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Address *</Label>
                    <Input
                      value={companyData.address}
                      onChange={(e) => setCompanyData({ ...companyData, address: e.target.value })}
                    />
                  </div>
                </div>

                <Button onClick={generateCoverLetter} className="w-full btn-primary mt-6">
                  <Download className="w-4 h-4 mr-2" />
                  Generate Cover Letter
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Company Profile */}
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Company Profile Generator</CardTitle>
                <CardDescription>Create comprehensive company profile document</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Company Name *</Label>
                    <Input
                      value={companyData.name}
                      onChange={(e) => setCompanyData({ ...companyData, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Year of Establishment *</Label>
                    <Input
                      value={companyData.established_year}
                      onChange={(e) => setCompanyData({ ...companyData, established_year: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>GST Number *</Label>
                    <Input
                      value={companyData.gst_number}
                      onChange={(e) => setCompanyData({ ...companyData, gst_number: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>PAN Number *</Label>
                    <Input
                      value={companyData.pan_number}
                      onChange={(e) => setCompanyData({ ...companyData, pan_number: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Website</Label>
                    <Input
                      value={companyData.website}
                      onChange={(e) => setCompanyData({ ...companyData, website: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Email *</Label>
                    <Input
                      type="email"
                      value={companyData.email}
                      onChange={(e) => setCompanyData({ ...companyData, email: e.target.value })}
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Registered Address *</Label>
                    <Textarea
                      value={companyData.address}
                      onChange={(e) => setCompanyData({ ...companyData, address: e.target.value })}
                      rows={3}
                    />
                  </div>
                </div>

                <Button onClick={generateCompanyProfile} className="w-full btn-primary mt-6">
                  <Download className="w-4 h-4 mr-2" />
                  Generate Company Profile
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* EMD Calculator */}
          <TabsContent value="calculator">
            <Card>
              <CardHeader>
                <CardTitle>EMD & Security Deposit Calculator</CardTitle>
                <CardDescription>Calculate Earnest Money Deposit and Security Deposit</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label>Tender Value (₹) *</Label>
                    <Input
                      type="number"
                      placeholder="Enter tender value"
                      value={tenderValue}
                      onChange={(e) => setTenderValue(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>EMD Percentage *</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={emdPercentage}
                      onChange={(e) => setEMDPercentage(parseFloat(e.target.value))}
                    />
                  </div>

                  <Button onClick={calculateEMD} className="w-full">
                    <Calculator className="w-4 h-4 mr-2" />
                    Calculate
                  </Button>

                  {emdResult && (
                    <div className="mt-6 p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg">
                      <h3 className="text-lg font-semibold text-slate-900 mb-4">Calculation Results</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-slate-600">Tender Value:</span>
                          <span className="font-semibold">₹{parseFloat(emdResult.tender_value).toLocaleString('en-IN')}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">EMD Percentage:</span>
                          <span className="font-semibold">{emdResult.emd_percentage}%</span>
                        </div>
                        <div className="flex justify-between text-lg border-t border-slate-300 pt-3">
                          <span className="font-bold text-slate-900">EMD Amount:</span>
                          <span className="font-bold text-blue-600">{emdResult.emd_amount_formatted}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Templates */}
          <TabsContent value="templates">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {templates.map((template) => (
                <Card key={template.id} className="hover:shadow-lg transition cursor-pointer">
                  <CardHeader>
                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-3">
                      <FileText className="w-6 h-6 text-blue-600" />
                    </div>
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    <CardDescription>{template.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button variant="outline" className="w-full">
                      <Download className="w-4 h-4 mr-2" />
                      Use Template
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default DocumentPreparationPage;
