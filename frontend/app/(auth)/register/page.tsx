import type { Metadata } from 'next';

import { RegisterForm } from '@/components/forms';

export const metadata: Metadata = {
  title: 'Create Account',
  description: 'Create your Multi-Agent Support account',
};

export default function RegisterPage() {
  return <RegisterForm />;
}
