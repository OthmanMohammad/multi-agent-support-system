import type { Metadata } from 'next';

import { LoginForm } from '@/components/forms';

export const metadata: Metadata = {
  title: 'Sign In',
  description: 'Sign in to your Multi-Agent Support account',
};

export default function LoginPage() {
  return <LoginForm />;
}
