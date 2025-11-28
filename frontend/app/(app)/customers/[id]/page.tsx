'use client';

import { ArrowLeft, Mail, Building, Phone, Globe, MessageSquare } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Avatar,
  AvatarFallback,
  Separator,
} from '@/components/ui';

// Mock customer data
const mockCustomer = {
  id: '1',
  name: 'John Smith',
  email: 'john@acme.com',
  phone: '+1 (555) 123-4567',
  company: 'Acme Corp',
  website: 'https://acme.com',
  tier: 'enterprise' as const,
  status: 'active' as const,
  healthScore: 92,
  lifetimeValue: 12500,
  lastContact: '2025-11-25',
  createdAt: '2024-06-15',
  conversations: 45,
  tickets: 12,
  notes:
    'Key enterprise customer. Interested in expanding to additional teams. Main contact for technical discussions.',
};

const recentActivity = [
  { id: '1', type: 'conversation', description: 'Support chat about billing', date: '2025-11-25' },
  { id: '2', type: 'ticket', description: 'Technical issue resolved', date: '2025-11-23' },
  { id: '3', type: 'conversation', description: 'Feature inquiry', date: '2025-11-20' },
];

export default function CustomerDetailPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button variant="ghost" onClick={() => router.back()} className="-ml-2">
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Customers
      </Button>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarFallback className="text-xl bg-brand-orange/10 text-brand-orange">
              {mockCustomer.name
                .split(' ')
                .map((n) => n[0])
                .join('')}
            </AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">{mockCustomer.name}</h1>
            <p className="text-text-secondary">{mockCustomer.company}</p>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="primary">{mockCustomer.tier}</Badge>
              <Badge variant="success">{mockCustomer.status}</Badge>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Mail className="h-4 w-4 mr-2" />
            Send Email
          </Button>
          <Link href="/chat">
            <Button>
              <MessageSquare className="h-4 w-4 mr-2" />
              Start Chat
            </Button>
          </Link>
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Main Info */}
        <div className="md:col-span-2 space-y-6">
          {/* Contact Info */}
          <Card>
            <CardHeader>
              <CardTitle>Contact Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background-secondary">
                    <Mail className="h-5 w-5 text-text-secondary" />
                  </div>
                  <div>
                    <p className="text-sm text-text-tertiary">Email</p>
                    <p className="font-medium text-text-primary">{mockCustomer.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background-secondary">
                    <Phone className="h-5 w-5 text-text-secondary" />
                  </div>
                  <div>
                    <p className="text-sm text-text-tertiary">Phone</p>
                    <p className="font-medium text-text-primary">{mockCustomer.phone}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background-secondary">
                    <Building className="h-5 w-5 text-text-secondary" />
                  </div>
                  <div>
                    <p className="text-sm text-text-tertiary">Company</p>
                    <p className="font-medium text-text-primary">{mockCustomer.company}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background-secondary">
                    <Globe className="h-5 w-5 text-text-secondary" />
                  </div>
                  <div>
                    <p className="text-sm text-text-tertiary">Website</p>
                    <a
                      href={mockCustomer.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-brand-orange-dark hover:underline"
                    >
                      {mockCustomer.website}
                    </a>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notes */}
          <Card>
            <CardHeader>
              <CardTitle>Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-text-secondary">{mockCustomer.notes}</p>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-background-secondary">
                      <MessageSquare className="h-4 w-4 text-text-secondary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text-primary">{activity.description}</p>
                      <p className="text-xs text-text-tertiary capitalize">{activity.type}</p>
                    </div>
                  </div>
                  <span className="text-sm text-text-tertiary">
                    {new Date(activity.date).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Health Score */}
          <Card>
            <CardHeader>
              <CardTitle>Health Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <div className="text-4xl font-bold text-success">{mockCustomer.healthScore}%</div>
                <p className="text-sm text-text-secondary mt-1">Healthy Customer</p>
              </div>
              <Separator className="my-4" />
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-text-secondary">Engagement</span>
                  <span className="font-medium text-text-primary">High</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Response Rate</span>
                  <span className="font-medium text-text-primary">95%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Satisfaction</span>
                  <span className="font-medium text-text-primary">4.8/5</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <span className="text-text-secondary">Lifetime Value</span>
                <span className="font-medium text-text-primary">
                  ${mockCustomer.lifetimeValue.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Conversations</span>
                <span className="font-medium text-text-primary">{mockCustomer.conversations}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Tickets</span>
                <span className="font-medium text-text-primary">{mockCustomer.tickets}</span>
              </div>
              <Separator />
              <div className="flex justify-between">
                <span className="text-text-secondary">Customer Since</span>
                <span className="font-medium text-text-primary">
                  {new Date(mockCustomer.createdAt).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Last Contact</span>
                <span className="font-medium text-text-primary">
                  {new Date(mockCustomer.lastContact).toLocaleDateString()}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
