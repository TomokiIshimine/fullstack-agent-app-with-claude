import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useForm } from './useForm'
import { validators } from '@/lib/validation'
import { ApiError } from '@/lib/api/client'

describe('useForm', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  describe('初期化', () => {
    it('初期値が正しく設定される', () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            email: { initialValue: 'test@example.com' },
            password: { initialValue: '' },
          },
        })
      )

      expect(result.current.values.email).toBe('test@example.com')
      expect(result.current.values.password).toBe('')
      expect(result.current.fields.email.value).toBe('test@example.com')
      expect(result.current.fields.password.value).toBe('')
    })

    it('初期状態が正しい', () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: '' },
          },
        })
      )

      expect(result.current.error).toBeNull()
      expect(result.current.isSubmitting).toBe(false)
      expect(result.current.isDirty).toBe(false)
    })
  })

  describe('フィールド値の変更', () => {
    it('onChangeでフィールド値が更新される', () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: '' },
          },
        })
      )

      act(() => {
        result.current.fields.name.onChange({
          target: { value: 'John' },
        } as React.ChangeEvent<HTMLInputElement>)
      })

      expect(result.current.values.name).toBe('John')
      expect(result.current.fields.name.value).toBe('John')
      expect(result.current.isDirty).toBe(true)
    })

    it('setValueでフィールド値が更新される', () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            count: { initialValue: 0 },
          },
        })
      )

      act(() => {
        result.current.fields.count.setValue(42)
      })

      expect(result.current.values.count).toBe(42)
      expect(result.current.isDirty).toBe(true)
    })

    it('フィールド変更時にフィールドエラーがクリアされる', async () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            email: {
              initialValue: '',
              validate: validators.required('必須'),
            },
          },
        })
      )

      // バリデーションエラーを発生させる
      await act(async () => {
        await result.current.handleSubmit(async () => {})({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(result.current.fields.email.error).toBe('必須')

      // フィールド変更でエラーがクリアされる
      act(() => {
        result.current.fields.email.onChange({
          target: { value: 'test@example.com' },
        } as React.ChangeEvent<HTMLInputElement>)
      })

      expect(result.current.fields.email.error).toBeUndefined()
    })
  })

  describe('バリデーション', () => {
    it('フィールドバリデーションが実行される', async () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            email: {
              initialValue: '',
              validate: validators.required('メールアドレスを入力してください'),
            },
          },
        })
      )

      await act(async () => {
        await result.current.handleSubmit(async () => {})({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(result.current.fields.email.error).toBe('メールアドレスを入力してください')
    })

    it('複合バリデーションが実行される', async () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            password: {
              initialValue: 'short',
              validate: validators.compose(
                validators.required('必須'),
                validators.minLength(8, '8文字以上')
              ),
            },
          },
        })
      )

      await act(async () => {
        await result.current.handleSubmit(async () => {})({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(result.current.fields.password.error).toBe('8文字以上')
    })

    it('フォームレベルバリデーションが実行される', async () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            password: { initialValue: 'password123' },
            confirmPassword: { initialValue: 'password456' },
          },
          validate: values => {
            if (values.password !== values.confirmPassword) {
              return 'パスワードが一致しません'
            }
            return null
          },
        })
      )

      await act(async () => {
        await result.current.handleSubmit(async () => {})({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(result.current.error).toBe('パスワードが一致しません')
    })

    it('matchバリデーションが正しく動作する', async () => {
      interface FormValues {
        password: string
        confirmPassword: string
      }

      const { result } = renderHook(() =>
        useForm<FormValues>({
          fields: {
            password: { initialValue: 'password123' },
            confirmPassword: {
              initialValue: 'password456',
              validate: validators.match<FormValues>('password', 'パスワードが一致しません'),
            },
          },
        })
      )

      await act(async () => {
        await result.current.handleSubmit(async () => {})({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(result.current.fields.confirmPassword.error).toBe('パスワードが一致しません')
    })
  })

  describe('フォーム送信', () => {
    it('バリデーション成功時にsubmitFnが呼ばれる', async () => {
      const submitFn = vi.fn()
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: 'John' },
          },
        })
      )

      await act(async () => {
        await result.current.handleSubmit(submitFn)({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(submitFn).toHaveBeenCalledWith({ name: 'John' })
    })

    it('バリデーション失敗時にsubmitFnが呼ばれない', async () => {
      const submitFn = vi.fn()
      const { result } = renderHook(() =>
        useForm({
          fields: {
            email: {
              initialValue: '',
              validate: validators.required('必須'),
            },
          },
        })
      )

      await act(async () => {
        await result.current.handleSubmit(submitFn)({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(submitFn).not.toHaveBeenCalled()
    })

    it('送信中はisSubmittingがtrueになる', async () => {
      let resolveSubmit: () => void
      const submitFn = vi.fn(
        () =>
          new Promise<void>(resolve => {
            resolveSubmit = resolve
          })
      )

      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: 'John' },
          },
        })
      )

      expect(result.current.isSubmitting).toBe(false)

      // 送信開始
      let submitPromise: Promise<void>
      act(() => {
        submitPromise = result.current.handleSubmit(submitFn)({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(result.current.isSubmitting).toBe(true)

      // 送信完了
      await act(async () => {
        resolveSubmit!()
        await submitPromise
      })

      expect(result.current.isSubmitting).toBe(false)
    })

    it('onSuccessが呼ばれる', async () => {
      const onSuccess = vi.fn()
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: 'John' },
          },
          onSuccess,
        })
      )

      await act(async () => {
        await result.current.handleSubmit(async () => {})({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(onSuccess).toHaveBeenCalled()
    })

    it('onBeforeSubmitでfalseを返すと送信がキャンセルされる', async () => {
      const submitFn = vi.fn()
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: 'John' },
          },
          onBeforeSubmit: () => false,
        })
      )

      await act(async () => {
        await result.current.handleSubmit(submitFn)({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(submitFn).not.toHaveBeenCalled()
    })
  })

  describe('エラーハンドリング', () => {
    it('ApiErrorのメッセージがセットされる', async () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            email: { initialValue: 'test@example.com' },
          },
        })
      )

      await act(async () => {
        await result.current.handleSubmit(async () => {
          throw new ApiError(400, 'メールアドレスが既に登録されています')
        })({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(result.current.error).toBe('メールアドレスが既に登録されています')
    })

    it('通常のErrorではdefaultErrorMessageがセットされる', async () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: 'John' },
          },
          defaultErrorMessage: 'ユーザー作成に失敗しました',
        })
      )

      await act(async () => {
        await result.current.handleSubmit(async () => {
          throw new Error('Network error')
        })({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      // Non-ApiError should use defaultErrorMessage, not the raw error message
      expect(result.current.error).toBe('ユーザー作成に失敗しました')
    })

    it('通常のErrorでdefaultErrorMessageがない場合はフォールバックメッセージがセットされる', async () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: 'John' },
          },
        })
      )

      await act(async () => {
        await result.current.handleSubmit(async () => {
          throw new Error('Network error')
        })({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      // Non-ApiError without defaultErrorMessage should use the fallback message
      expect(result.current.error).toBe('エラーが発生しました')
    })

    it('不明なエラーはデフォルトメッセージがセットされる', async () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: 'John' },
          },
          defaultErrorMessage: 'エラーが発生しました',
        })
      )

      await act(async () => {
        await result.current.handleSubmit(async () => {
          throw 'unknown error'
        })({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(result.current.error).toBe('エラーが発生しました')
    })

    it('clearErrorでエラーがクリアされる', async () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: '' },
          },
        })
      )

      act(() => {
        result.current.setError('テストエラー')
      })

      expect(result.current.error).toBe('テストエラー')

      act(() => {
        result.current.clearError()
      })

      expect(result.current.error).toBeNull()
    })
  })

  describe('リセット', () => {
    it('resetで初期値に戻る', () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: 'Initial' },
          },
        })
      )

      act(() => {
        result.current.fields.name.onChange({
          target: { value: 'Changed' },
        } as React.ChangeEvent<HTMLInputElement>)
      })

      expect(result.current.values.name).toBe('Changed')
      expect(result.current.isDirty).toBe(true)

      act(() => {
        result.current.reset()
      })

      expect(result.current.values.name).toBe('Initial')
      expect(result.current.isDirty).toBe(false)
    })

    it('resetでエラーもクリアされる', async () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            email: {
              initialValue: '',
              validate: validators.required('必須'),
            },
          },
        })
      )

      await act(async () => {
        await result.current.handleSubmit(async () => {})({
          preventDefault: vi.fn(),
        } as unknown as React.FormEvent)
      })

      expect(result.current.fields.email.error).toBe('必須')

      act(() => {
        result.current.reset()
      })

      expect(result.current.fields.email.error).toBeUndefined()
      expect(result.current.error).toBeNull()
    })
  })

  describe('setInitialValues', () => {
    it('初期値を更新できる', () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: '' },
            email: { initialValue: '' },
          },
        })
      )

      act(() => {
        result.current.setInitialValues({
          name: 'John',
          email: 'john@example.com',
        })
      })

      expect(result.current.values.name).toBe('John')
      expect(result.current.values.email).toBe('john@example.com')
      expect(result.current.isDirty).toBe(false)
    })

    it('部分的な更新ができる', () => {
      const { result } = renderHook(() =>
        useForm({
          fields: {
            name: { initialValue: 'Initial' },
            email: { initialValue: 'initial@example.com' },
          },
        })
      )

      act(() => {
        result.current.setInitialValues({
          name: 'Updated',
        })
      })

      expect(result.current.values.name).toBe('Updated')
      expect(result.current.values.email).toBe('initial@example.com')
    })
  })
})
