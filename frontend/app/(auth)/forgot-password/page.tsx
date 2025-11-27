import type { Metadata } from 'next';

import { ForgotPasswordForm } from '@/components/forms';

export const metadata: Metadata = {
  title: 'Forgot Password',
  description: 'Reset your Multi-Agent Support password',
};

export default function ForgotPasswordPage() {
  return <ForgotPasswordForm />;
}
