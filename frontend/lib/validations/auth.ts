import { z } from 'zod';

// =============================================================================
// Password validation helper
// =============================================================================

const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .max(128, 'Password must be less than 128 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number')
  .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character');

// =============================================================================
// Login Schema
// =============================================================================

export const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

export type LoginFormData = z.infer<typeof loginSchema>;

// =============================================================================
// Register Schema
// =============================================================================

export const registerSchema = z
  .object({
    email: z.string().email('Please enter a valid email address'),
    full_name: z
      .string()
      .min(1, 'Full name is required')
      .max(255, 'Full name must be less than 255 characters'),
    organization: z.string().max(255, 'Organization must be less than 255 characters').optional(),
    password: passwordSchema,
    confirm_password: z.string().min(1, 'Please confirm your password'),
    turnstile_token: z.string().min(1, 'Please complete the captcha'),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;

// =============================================================================
// Forgot Password Schema
// =============================================================================

export const forgotPasswordSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
});

export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

// =============================================================================
// Reset Password Schema
// =============================================================================

export const resetPasswordSchema = z
  .object({
    token: z.string().min(1, 'Reset token is required'),
    new_password: passwordSchema,
    confirm_password: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;
