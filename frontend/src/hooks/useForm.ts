import { useState, useCallback, useMemo } from 'react'
import type { FormEvent, ChangeEvent } from 'react'
import { ApiError } from '@/lib/api/client'
import { logger } from '@/lib/logger'
import type { ValidatorFn } from '@/lib/validation'

/**
 * Configuration for a single form field
 */
export interface FieldConfig<T> {
  /** Initial value of the field */
  initialValue: T
  /** Validation function that returns error message or null */
  validate?: ValidatorFn<T>
}

/**
 * Generic form values type
 */
export type FormValues = Record<string, unknown>

/**
 * Form field state with value and change handler
 */
export interface FormField<T> {
  /** Current field value */
  value: T
  /** Change handler for input elements */
  onChange: (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  /** Direct value setter for non-input updates */
  setValue: (value: T) => void
  /** Field-level error message */
  error?: string
}

/**
 * Form state returned by useForm hook
 */
export interface FormState<T extends FormValues> {
  /** Individual field states */
  fields: { [K in keyof T]: FormField<T[K]> }
  /** Combined field values */
  values: T
  /** Form-level error message */
  error: string | null
  /** Whether form is currently submitting */
  isSubmitting: boolean
  /** Whether form has been modified */
  isDirty: boolean
  /** Clear error state */
  clearError: () => void
  /** Reset form to initial values */
  reset: () => void
  /** Set form-level error */
  setError: (error: string | null) => void
  /** Handle form submission with validation and API error handling */
  handleSubmit: (submitFn: (values: T) => Promise<void>) => (e: FormEvent) => Promise<void>
  /** Update initial values (useful for edit forms with async data) */
  setInitialValues: (values: Partial<T>) => void
}

/**
 * Options for useForm hook
 */
export interface UseFormOptions<T extends FormValues> {
  /** Field configurations with initial values and optional validators */
  fields: { [K in keyof T]: FieldConfig<T[K]> }
  /** Form-level validation (runs after field validation) */
  validate?: (values: T) => string | null
  /** Custom error message for non-ApiError exceptions */
  defaultErrorMessage?: string
  /** Called on successful submission */
  onSuccess?: () => void
  /** Called before submission starts (return false to prevent) */
  onBeforeSubmit?: (values: T) => boolean | void
}

/**
 * Generic form hook that handles form state, validation, and submission.
 *
 * Features:
 * - Field-level and form-level validation
 * - ApiError handling with automatic error message extraction
 * - Submission state management (isSubmitting)
 * - Dirty state tracking
 * - Reset functionality
 *
 * @example
 * ```typescript
 * const form = useForm<{ email: string; password: string }>({
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
 *       validate: validators.required('パスワードを入力してください'),
 *     },
 *   },
 *   defaultErrorMessage: 'ログインに失敗しました',
 *   onSuccess: () => navigate('/dashboard'),
 * })
 *
 * const onSubmit = form.handleSubmit(async (values) => {
 *   await login(values)
 * })
 *
 * return (
 *   <form onSubmit={onSubmit}>
 *     {form.error && <Alert variant="error">{form.error}</Alert>}
 *     <Input
 *       value={form.fields.email.value}
 *       onChange={form.fields.email.onChange}
 *       error={form.fields.email.error}
 *     />
 *     <Button loading={form.isSubmitting}>ログイン</Button>
 *   </form>
 * )
 * ```
 */
export function useForm<T extends FormValues>(options: UseFormOptions<T>): FormState<T> {
  const { fields: fieldConfigs, validate, defaultErrorMessage, onSuccess, onBeforeSubmit } = options

  // Compute initial values from config - memoized to prevent recreating on each render
  const initialValues = useMemo(() => {
    const values: Record<string, unknown> = {}
    for (const [key, config] of Object.entries(fieldConfigs)) {
      values[key] = (config as FieldConfig<unknown>).initialValue
    }
    return values as T
  }, [fieldConfigs])

  const [values, setValues] = useState<T>(initialValues)
  const [currentInitialValues, setCurrentInitialValues] = useState<T>(initialValues)
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof T, string>>>({})
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDirty, setIsDirty] = useState(false)

  const clearError = useCallback(() => setError(null), [])

  const reset = useCallback(() => {
    setValues(currentInitialValues)
    setFieldErrors({})
    setError(null)
    setIsDirty(false)
  }, [currentInitialValues])

  const setInitialValues = useCallback((newValues: Partial<T>) => {
    setCurrentInitialValues(prev => {
      const updated = { ...prev, ...newValues }
      setValues(updated)
      return updated
    })
    setIsDirty(false)
  }, [])

  const setFieldValue = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
    setValues(prev => ({ ...prev, [field]: value }))
    setIsDirty(true)
    // Clear field error on change
    setFieldErrors(prev => ({ ...prev, [field]: undefined }))
  }, [])

  const runValidation = useCallback((): boolean => {
    const errors: Partial<Record<keyof T, string>> = {}
    let hasError = false

    // Run field-level validation
    for (const [key, config] of Object.entries(fieldConfigs) as [
      keyof T,
      FieldConfig<T[keyof T]>,
    ][]) {
      if (config.validate) {
        const fieldError = config.validate(values[key], values as Record<string, unknown>)
        if (fieldError) {
          errors[key] = fieldError
          hasError = true
        }
      }
    }

    setFieldErrors(errors)

    // Run form-level validation only if no field errors
    if (!hasError && validate) {
      const formError = validate(values)
      if (formError) {
        setError(formError)
        return false
      }
    }

    return !hasError
  }, [fieldConfigs, validate, values])

  const handleSubmit = useCallback(
    (submitFn: (values: T) => Promise<void>) => async (e: FormEvent) => {
      e.preventDefault()
      setError(null)

      // Pre-submit check
      if (onBeforeSubmit && onBeforeSubmit(values) === false) {
        return
      }

      // Validation
      if (!runValidation()) {
        return
      }

      setIsSubmitting(true)

      try {
        await submitFn(values)
        onSuccess?.()
      } catch (err) {
        logger.error('Form submission failed', err as Error)
        if (err instanceof ApiError) {
          // ApiError has a localized message from the backend
          setError(err.message)
        } else {
          // Non-ApiError (network errors, etc.) should use the default message
          setError(defaultErrorMessage || 'エラーが発生しました')
        }
      } finally {
        setIsSubmitting(false)
      }
    },
    [values, runValidation, onBeforeSubmit, onSuccess, defaultErrorMessage]
  )

  // Build fields object with getters/setters
  const fields = useMemo(() => {
    const result: Record<string, FormField<unknown>> = {}
    for (const key of Object.keys(fieldConfigs) as (keyof T)[]) {
      result[key as string] = {
        value: values[key],
        onChange: (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
          setFieldValue(key, e.target.value as T[typeof key]),
        setValue: (value: T[typeof key]) => setFieldValue(key, value),
        error: fieldErrors[key],
      }
    }
    return result as { [K in keyof T]: FormField<T[K]> }
  }, [fieldConfigs, values, fieldErrors, setFieldValue])

  return {
    fields,
    values,
    error,
    isSubmitting,
    isDirty,
    clearError,
    reset,
    setError,
    handleSubmit,
    setInitialValues,
  }
}
