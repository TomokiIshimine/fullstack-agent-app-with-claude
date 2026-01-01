import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Utility function to merge Tailwind CSS classes with proper conflict resolution.
 *
 * Combines clsx for conditional class handling and tailwind-merge for
 * intelligent Tailwind class merging (e.g., avoiding "p-2 p-4" conflicts).
 *
 * @example
 * cn('px-2 py-1', 'p-4') // => 'p-4' (tailwind-merge resolves conflict)
 * cn('text-red-500', isActive && 'text-blue-500') // conditional classes
 * cn(baseStyles, variantStyles[variant], className) // component patterns
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
