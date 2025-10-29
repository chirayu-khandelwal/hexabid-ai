import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API, AuthContext } from '../App';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Plus, Mail, Phone, Building2 } from 'lucide-react';

const CRMPage = () => {
  const { user, logout } = useContext(AuthContext);
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newContact, setNewContact] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    type: 'vendor',
    notes: ''
  });

  useEffect(() => {
    fetchContacts();
  }, [filter]);

  const fetchContacts = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = filter ? `?contact_type=${filter}` : '';
      const response = await axios.get(`${API}/crm/contacts${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setContacts(response.data);
    } catch (error) {
      toast.error('Failed to load contacts');
    } finally {
      setLoading(false);
    }
  };

  const handleAddContact = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/crm/contacts`, newContact, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Contact added successfully');
      setIsAddOpen(false);
      setNewContact({
        name: '',
        email: '',
        phone: '',
        company: '',
        type: 'vendor',
        notes: ''
      });
      fetchContacts();
    } catch (error) {
      toast.error('Failed to add contact');
    }
  };

  return (
    <Layout user={user} onLogout={logout}>
      <div className="p-8" data-testid="crm-page">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900" data-testid="crm-title">CRM & Contacts</h1>
            <p className="text-slate-600 mt-1">Manage your vendors, OEMs, and clients</p>
          </div>
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button className="btn-primary" data-testid="add-contact-btn">
                <Plus className="w-4 h-4 mr-2" />
                Add Contact
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Contact</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleAddContact} className="space-y-4" data-testid="add-contact-form">
                <div>
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={newContact.name}
                    onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                    required
                    data-testid="contact-name-input"
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={newContact.email}
                    onChange={(e) => setNewContact({ ...newContact, email: e.target.value })}
                    required
                    data-testid="contact-email-input"
                  />
                </div>
                <div>
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    value={newContact.phone}
                    onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })}
                    data-testid="contact-phone-input"
                  />
                </div>
                <div>
                  <Label htmlFor="company">Company</Label>
                  <Input
                    id="company"
                    value={newContact.company}
                    onChange={(e) => setNewContact({ ...newContact, company: e.target.value })}
                    data-testid="contact-company-input"
                  />
                </div>
                <div>
                  <Label htmlFor="type">Type *</Label>
                  <select
                    id="type"
                    value={newContact.type}
                    onChange={(e) => setNewContact({ ...newContact, type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md"
                    data-testid="contact-type-select"
                  >
                    <option value="vendor">Vendor</option>
                    <option value="oem">OEM</option>
                    <option value="client">Client</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="notes">Notes</Label>
                  <textarea
                    id="notes"
                    value={newContact.notes}
                    onChange={(e) => setNewContact({ ...newContact, notes: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md"
                    rows={3}
                    data-testid="contact-notes-input"
                  />
                </div>
                <Button type="submit" className="w-full btn-primary" data-testid="save-contact-btn">
                  Save Contact
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="mb-6 flex gap-2">
          <Button
            variant={filter === '' ? 'default' : 'outline'}
            onClick={() => setFilter('')}
            data-testid="filter-all"
          >
            All
          </Button>
          <Button
            variant={filter === 'vendor' ? 'default' : 'outline'}
            onClick={() => setFilter('vendor')}
            data-testid="filter-vendor"
          >
            Vendors
          </Button>
          <Button
            variant={filter === 'oem' ? 'default' : 'outline'}
            onClick={() => setFilter('oem')}
            data-testid="filter-oem"
          >
            OEMs
          </Button>
          <Button
            variant={filter === 'client' ? 'default' : 'outline'}
            onClick={() => setFilter('client')}
            data-testid="filter-client"
          >
            Clients
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="loader"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="contacts-list">
            {contacts.length === 0 ? (
              <div className="col-span-full text-center py-20" data-testid="no-contacts">
                <p className="text-slate-500 mb-4">No contacts found</p>
                <p className="text-sm text-slate-400">Add your first contact to get started</p>
              </div>
            ) : (
              contacts.map((contact) => (
                <div
                  key={contact.id}
                  className="bg-white rounded-lg p-5 shadow-sm border border-slate-200 hover:shadow-md transition"
                  data-testid={`contact-card-${contact.id}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                        {contact.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900" data-testid="contact-name">{contact.name}</h3>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          contact.type === 'vendor' ? 'bg-blue-100 text-blue-600' :
                          contact.type === 'oem' ? 'bg-purple-100 text-purple-600' :
                          'bg-green-100 text-green-600'
                        }`}>
                          {contact.type}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    {contact.company && (
                      <div className="flex items-center gap-2 text-slate-600">
                        <Building2 className="w-4 h-4" />
                        <span>{contact.company}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-slate-600">
                      <Mail className="w-4 h-4" />
                      <span className="truncate" data-testid="contact-email">{contact.email}</span>
                    </div>
                    {contact.phone && (
                      <div className="flex items-center gap-2 text-slate-600">
                        <Phone className="w-4 h-4" />
                        <span>{contact.phone}</span>
                      </div>
                    )}
                  </div>
                  
                  {contact.notes && (
                    <p className="mt-3 text-xs text-slate-500 line-clamp-2">{contact.notes}</p>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default CRMPage;
