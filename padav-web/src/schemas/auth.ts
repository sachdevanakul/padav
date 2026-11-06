import { z } from 'zod'

export const loginSchema = z.object({
  email: z.email('Enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

export const registerSchema = loginSchema.extend({
  full_name: z.string().trim().min(2, 'Enter your full name'),
  confirm_password: z.string().min(8, 'Confirm your password'),
}).refine((data) => data.password === data.confirm_password, {
  path: ['confirm_password'],
  message: 'Passwords do not match',
})

export type LoginValues = z.infer<typeof loginSchema>
export type RegisterValues = z.infer<typeof registerSchema>
