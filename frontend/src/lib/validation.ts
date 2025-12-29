/**
 * Validation utilities for form fields
 *
 * Usage:
 * ```typescript
 * import { validators } from '@/lib/validation'
 *
 * const form = useForm({
 *   fields: {
 *     email: {
 *       initialValue: '',
 *       validate: validators.compose(
 *         validators.required('メールアドレスを入力してください'),
 *         validators.email()
 *       ),
 *     },
 *     password: {
 *       initialValue: '',
 *       validate: validators.compose(
 *         validators.required('パスワードを入力してください'),
 *         validators.minLength(8, 'パスワードは8文字以上で入力してください')
 *       ),
 *     },
 *   },
 * })
 * ```
 */

/**
 * Validator function type
 * Returns error message if validation fails, null if valid
 */
export type ValidatorFn<T = unknown> = (
  value: T,
  allValues?: Record<string, unknown>
) => string | null

/**
 * Email pattern for validation
 */
const EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/

/**
 * Collection of common validators
 */
export const validators = {
  /**
   * Validates that a value is not empty
   * @param message - Custom error message (default: 'この項目は必須です')
   */
  required:
    (message = 'この項目は必須です'): ValidatorFn =>
    (value: unknown): string | null => {
      if (value === '' || value === null || value === undefined) {
        return message
      }
      return null
    },

  /**
   * Validates minimum string length
   * @param min - Minimum length
   * @param message - Custom error message
   */
  minLength:
    (min: number, message?: string): ValidatorFn<string> =>
    (value: string): string | null => {
      if (value.length < min) {
        return message || `${min}文字以上で入力してください`
      }
      return null
    },

  /**
   * Validates maximum string length
   * @param max - Maximum length
   * @param message - Custom error message
   */
  maxLength:
    (max: number, message?: string): ValidatorFn<string> =>
    (value: string): string | null => {
      if (value.length > max) {
        return message || `${max}文字以内で入力してください`
      }
      return null
    },

  /**
   * Validates email format
   * @param message - Custom error message (default: 'メールアドレスの形式が正しくありません')
   */
  email:
    (message = 'メールアドレスの形式が正しくありません'): ValidatorFn<string> =>
    (value: string): string | null => {
      if (value && !EMAIL_PATTERN.test(value.trim())) {
        return message
      }
      return null
    },

  /**
   * Validates that a value matches another field
   * @param field - Field name to match against
   * @param message - Error message when values don't match
   */
  match:
    <T extends Record<string, unknown>>(field: keyof T, message: string): ValidatorFn =>
    (value: unknown, allValues?: Record<string, unknown>): string | null => {
      if (allValues && value !== allValues[field as string]) {
        return message
      }
      return null
    },

  /**
   * Validates that a value does NOT match another field
   * @param field - Field name to compare against
   * @param message - Error message when values match
   */
  notMatch:
    <T extends Record<string, unknown>>(field: keyof T, message: string): ValidatorFn =>
    (value: unknown, allValues?: Record<string, unknown>): string | null => {
      if (allValues && value === allValues[field as string]) {
        return message
      }
      return null
    },

  /**
   * Validates using a custom regex pattern
   * @param pattern - RegExp to test against
   * @param message - Error message when pattern doesn't match
   */
  pattern:
    (pattern: RegExp, message: string): ValidatorFn<string> =>
    (value: string): string | null => {
      if (value && !pattern.test(value)) {
        return message
      }
      return null
    },

  /**
   * Composes multiple validators into a single validator
   * Runs validators in order, returns first error encountered
   * @param fns - Validators to compose
   */
  compose:
    <T = unknown>(...fns: ValidatorFn<T>[]): ValidatorFn<T> =>
    (value: T, allValues?: Record<string, unknown>): string | null => {
      for (const validate of fns) {
        const error = validate(value, allValues)
        if (error) return error
      }
      return null
    },
}
