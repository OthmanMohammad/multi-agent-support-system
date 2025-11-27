'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Search,
  Filter,
  MoreHorizontal,
  Mail,
  Building,
  Calendar,
  ArrowUpRight,
} from 'lucide-react';

import {
  Button,
  Input,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Avatar,
  AvatarFallback,
} from '@/components/ui';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';

interface Customer {
  id: string;
  name: string;
  email: string;
  company: string;
  tier: 'free' | 'starter' | 'professional' | 'enterprise';
  status: 'active' | 'churned' | 'at_risk' | 'new';
  healthScore: number;
  lastContact: string;
}

const mockCustomers: Customer[] = [
  {
    id: '1',
    name: 'John Smith',
    email: 'john@acme.com',
    company: 'Acme Corp',
    tier: 'enterprise',
    status: 'active',
    healthScore: 92,
    lastContact: '2025-11-25',
  },
  {
    id: '2',
    name: 'Sarah Johnson',
    email: 'sarah@techstart.io',
    company: 'TechStart',
    tier: 'professional',
    status: 'active',
    healthScore: 78,
    lastContact: '2025-11-24',
  },
  {
    id: '3',
    name: 'Mike Davis',
    email: 'mike@growthco.com',
    company: 'GrowthCo',
    tier: 'starter',
    status: 'at_risk',
    healthScore: 45,
    lastContact: '2025-11-15',
  },
  {
    id: '4',
    name: 'Emily Chen',
    email: 'emily@newco.com',
    company: 'NewCo',
    tier: 'free',
    status: 'new',
    healthScore: 100,
    lastContact: '2025-11-27',
  },
];

const tierColors = {
  free: 'default',
  starter: 'info',
  professional: 'warning',
  enterprise: 'primary',
} as const;

const statusColors = {
  active: 'success',
  churned: 'error',
  at_risk: 'warning',
  new: 'info',
} as const;

export default function CustomersPage() {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredCustomers = mockCustomers.filter(
    (customer) =>
      customer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      customer.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      customer.company.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Customers</h1>
          <p className="text-text-secondary">Manage and view customer information</p>
        </div>
        <Button>
          <Mail className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-text-secondary">Total Customers</p>
            <p className="text-2xl font-bold text-text-primary">{mockCustomers.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-text-secondary">Active</p>
            <p className="text-2xl font-bold text-success">
              {mockCustomers.filter((c) => c.status === 'active').length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-text-secondary">At Risk</p>
            <p className="text-2xl font-bold text-warning">
              {mockCustomers.filter((c) => c.status === 'at_risk').length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-text-secondary">New This Month</p>
            <p className="text-2xl font-bold text-info">
              {mockCustomers.filter((c) => c.status === 'new').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filter */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-tertiary" />
          <Input
            placeholder="Search customers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline">
          <Filter className="h-4 w-4 mr-2" />
          Filter
        </Button>
      </div>

      {/* Customer List */}
      <Card>
        <CardHeader>
          <CardTitle>All Customers</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-border">
            {filteredCustomers.map((customer) => (
              <div
                key={customer.id}
                className="flex items-center justify-between p-4 hover:bg-background-secondary/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <Avatar>
                    <AvatarFallback className="bg-brand-orange/10 text-brand-orange">
                      {customer.name
                        .split(' ')
                        .map((n) => n[0])
                        .join('')}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-medium text-text-primary">{customer.name}</p>
                    <div className="flex items-center gap-3 text-sm text-text-secondary">
                      <span className="flex items-center gap-1">
                        <Mail className="h-3 w-3" />
                        {customer.email}
                      </span>
                      <span className="flex items-center gap-1">
                        <Building className="h-3 w-3" />
                        {customer.company}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <Badge variant={tierColors[customer.tier]}>{customer.tier}</Badge>
                  </div>
                  <div className="text-right">
                    <Badge variant={statusColors[customer.status]}>{customer.status}</Badge>
                  </div>
                  <div className="text-right w-20">
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          'h-2 w-2 rounded-full',
                          customer.healthScore >= 70
                            ? 'bg-success'
                            : customer.healthScore >= 40
                              ? 'bg-warning'
                              : 'bg-error'
                        )}
                      />
                      <span className="text-sm font-medium">{customer.healthScore}%</span>
                    </div>
                    <p className="text-xs text-text-tertiary">Health</p>
                  </div>
                  <div className="text-right w-24">
                    <p className="text-sm text-text-primary flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {new Date(customer.lastContact).toLocaleDateString()}
                    </p>
                    <p className="text-xs text-text-tertiary">Last Contact</p>
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon-sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem asChild>
                        <Link href={`/customers/${customer.id}`}>
                          View Details
                          <ArrowUpRight className="h-4 w-4 ml-auto" />
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem>Send Message</DropdownMenuItem>
                      <DropdownMenuItem>View Conversations</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
