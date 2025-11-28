'use client';

import { User, Lock, Bell, CreditCard, Building, Shield } from 'lucide-react';
import { useState } from 'react';

import {
  Button,
  Input,
  Label,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Separator,
  Avatar,
  AvatarFallback,
} from '@/components/ui';
import { useAuthStore } from '@/lib/stores/auth-store';
import { cn } from '@/lib/utils';

type SettingsTab = 'profile' | 'password' | 'notifications' | 'billing' | 'team' | 'security';

interface TabItem {
  id: SettingsTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const tabs: TabItem[] = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'password', label: 'Password', icon: Lock },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'billing', label: 'Billing', icon: CreditCard },
  { id: 'team', label: 'Team', icon: Building },
  { id: 'security', label: 'Security', icon: Shield },
];

function ProfileSettings() {
  const { user } = useAuthStore();

  const userInitials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U';

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-text-primary">Profile Information</h3>
        <p className="text-sm text-text-secondary">
          Update your personal information and how others see you.
        </p>
      </div>

      <Separator />

      <div className="flex items-center gap-6">
        <Avatar className="h-20 w-20">
          <AvatarFallback className="text-xl bg-brand-orange text-white">
            {userInitials}
          </AvatarFallback>
        </Avatar>
        <div>
          <Button variant="outline" size="sm">
            Change Avatar
          </Button>
          <p className="text-xs text-text-tertiary mt-2">JPG, GIF or PNG. Max 2MB.</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="fullName">Full Name</Label>
          <Input id="fullName" defaultValue={user?.full_name || ''} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" defaultValue={user?.email || ''} disabled />
          <p className="text-xs text-text-tertiary">Contact support to change your email.</p>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="company">Company</Label>
        <Input id="company" placeholder="Your company name" />
      </div>

      <div className="flex justify-end">
        <Button>Save Changes</Button>
      </div>
    </div>
  );
}

function PasswordSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-text-primary">Change Password</h3>
        <p className="text-sm text-text-secondary">
          Update your password to keep your account secure.
        </p>
      </div>

      <Separator />

      <div className="max-w-md space-y-4">
        <div className="space-y-2">
          <Label htmlFor="currentPassword">Current Password</Label>
          <Input id="currentPassword" type="password" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="newPassword">New Password</Label>
          <Input id="newPassword" type="password" />
          <p className="text-xs text-text-tertiary">
            Minimum 8 characters with uppercase, lowercase, and numbers.
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirmPassword">Confirm New Password</Label>
          <Input id="confirmPassword" type="password" />
        </div>
      </div>

      <div className="flex justify-end">
        <Button>Update Password</Button>
      </div>
    </div>
  );
}

function NotificationSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-text-primary">Notification Preferences</h3>
        <p className="text-sm text-text-secondary">
          Choose how you want to be notified about activity.
        </p>
      </div>

      <Separator />

      <div className="space-y-4">
        {[
          {
            title: 'New conversations',
            description: 'Get notified when a new conversation is started',
          },
          {
            title: 'Escalations',
            description: 'Get notified when a conversation is escalated to you',
          },
          {
            title: 'Weekly reports',
            description: 'Receive weekly summary reports via email',
          },
          {
            title: 'Product updates',
            description: 'Stay informed about new features and updates',
          },
        ].map((item) => (
          <div
            key={item.title}
            className="flex items-center justify-between py-3 border-b border-border last:border-0"
          >
            <div>
              <p className="font-medium text-text-primary">{item.title}</p>
              <p className="text-sm text-text-secondary">{item.description}</p>
            </div>
            <label className="relative inline-flex cursor-pointer items-center">
              <input type="checkbox" className="peer sr-only" defaultChecked />
              <div className="h-6 w-11 rounded-full bg-background-tertiary peer-checked:bg-brand-orange transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-transform peer-checked:after:translate-x-5" />
            </label>
          </div>
        ))}
      </div>

      <div className="flex justify-end">
        <Button>Save Preferences</Button>
      </div>
    </div>
  );
}

function BillingSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-text-primary">Billing & Plans</h3>
        <p className="text-sm text-text-secondary">Manage your subscription and payment methods.</p>
      </div>

      <Separator />

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Current Plan</p>
              <p className="text-2xl font-bold text-text-primary">Professional</p>
              <p className="text-sm text-text-secondary">$49/month, billed monthly</p>
            </div>
            <Button variant="outline">Change Plan</Button>
          </div>
        </CardContent>
      </Card>

      <div>
        <h4 className="font-medium text-text-primary mb-4">Payment Method</h4>
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-16 bg-background-secondary rounded flex items-center justify-center">
                <CreditCard className="h-5 w-5 text-text-secondary" />
              </div>
              <div>
                <p className="font-medium text-text-primary">**** **** **** 4242</p>
                <p className="text-sm text-text-secondary">Expires 12/2025</p>
              </div>
            </div>
            <Button variant="ghost" size="sm">
              Edit
            </Button>
          </CardContent>
        </Card>
      </div>

      <div>
        <h4 className="font-medium text-text-primary mb-4">Billing History</h4>
        <Card>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {[
                { date: 'Nov 1, 2025', amount: '$49.00', status: 'Paid' },
                { date: 'Oct 1, 2025', amount: '$49.00', status: 'Paid' },
                { date: 'Sep 1, 2025', amount: '$49.00', status: 'Paid' },
              ].map((invoice) => (
                <div key={invoice.date} className="flex items-center justify-between p-4">
                  <div>
                    <p className="font-medium text-text-primary">{invoice.date}</p>
                    <p className="text-sm text-text-secondary">{invoice.amount}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-success">{invoice.status}</span>
                    <Button variant="ghost" size="sm">
                      Download
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function TeamSettings() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-text-primary">Team Members</h3>
          <p className="text-sm text-text-secondary">Manage who has access to your workspace.</p>
        </div>
        <Button>Invite Member</Button>
      </div>

      <Separator />

      <Card>
        <CardContent className="p-0">
          <div className="divide-y divide-border">
            {[
              { name: 'You', email: 'you@example.com', role: 'Owner' },
              { name: 'John Doe', email: 'john@example.com', role: 'Admin' },
              { name: 'Jane Smith', email: 'jane@example.com', role: 'Member' },
            ].map((member) => (
              <div key={member.email} className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <Avatar>
                    <AvatarFallback className="bg-brand-orange/10 text-brand-orange">
                      {member.name
                        .split(' ')
                        .map((n) => n[0])
                        .join('')}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-medium text-text-primary">{member.name}</p>
                    <p className="text-sm text-text-secondary">{member.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-text-secondary">{member.role}</span>
                  {member.role !== 'Owner' && (
                    <Button variant="ghost" size="sm">
                      Remove
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function SecuritySettings() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-text-primary">Security Settings</h3>
        <p className="text-sm text-text-secondary">
          Manage your account security and authentication.
        </p>
      </div>

      <Separator />

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Two-Factor Authentication</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">
                  Add an extra layer of security to your account.
                </p>
                <p className="text-sm text-warning mt-1">Not enabled</p>
              </div>
              <Button variant="outline">Enable 2FA</Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Active Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { device: 'Chrome on macOS', location: 'San Francisco, CA', current: true },
                { device: 'Safari on iPhone', location: 'San Francisco, CA', current: false },
              ].map((session, index) => (
                <div key={index} className="flex items-center justify-between py-2">
                  <div>
                    <p className="font-medium text-text-primary">
                      {session.device}
                      {session.current && (
                        <span className="ml-2 text-xs text-success">(Current)</span>
                      )}
                    </p>
                    <p className="text-sm text-text-secondary">{session.location}</p>
                  </div>
                  {!session.current && (
                    <Button variant="ghost" size="sm" className="text-error">
                      Revoke
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-error/50">
          <CardHeader>
            <CardTitle className="text-base text-error">Danger Zone</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-text-primary">Delete Account</p>
                <p className="text-sm text-text-secondary">
                  Permanently delete your account and all data.
                </p>
              </div>
              <Button variant="outline" className="text-error border-error hover:bg-error/10">
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

const tabComponents: Record<SettingsTab, React.ComponentType> = {
  profile: ProfileSettings,
  password: PasswordSettings,
  notifications: NotificationSettings,
  billing: BillingSettings,
  team: TeamSettings,
  security: SecuritySettings,
};

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const ActiveComponent = tabComponents[activeTab];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Settings</h1>
        <p className="text-text-secondary">Manage your account and preferences</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Navigation */}
        <Card className="lg:w-64 shrink-0">
          <CardContent className="p-2">
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                    activeTab === tab.id
                      ? 'bg-brand-orange/10 text-brand-orange'
                      : 'text-text-secondary hover:bg-background-secondary hover:text-text-primary'
                  )}
                >
                  <tab.icon className="h-4 w-4" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </CardContent>
        </Card>

        {/* Content */}
        <Card className="flex-1">
          <CardContent className="p-6">
            <ActiveComponent />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
