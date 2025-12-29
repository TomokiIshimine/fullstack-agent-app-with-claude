import type { UserCreateRequest, UserCreateResponse } from '@/types/user'
import { createUser as createUserApi } from '@/lib/api/users'
import { logger } from '@/lib/logger'
import { Input, Button, Alert } from '@/components/ui'
import { useForm } from '@/hooks/useForm'
import { validators } from '@/lib/validation'

interface UserCreateFormProps {
  onCreate?: (payload: UserCreateRequest) => Promise<UserCreateResponse>
  onSuccess?: (response: UserCreateResponse) => void
  onCancel: () => void
}

interface UserCreateFormValues {
  email: string
  name: string
}

export function UserCreateForm({ onCreate, onSuccess, onCancel }: UserCreateFormProps) {
  const form = useForm<UserCreateFormValues>({
    fields: {
      email: {
        initialValue: '',
        validate: validators.compose(
          validators.required('メールアドレスを入力してください'),
          validators.email('メールアドレスの形式が正しくありません')
        ),
      },
      name: {
        initialValue: '',
        validate: validators.compose(
          validators.required('名前を入力してください'),
          validators.maxLength(100, '名前は100文字以内で入力してください')
        ),
      },
    },
    defaultErrorMessage: 'ユーザーの作成に失敗しました',
  })

  const handleSubmit = form.handleSubmit(async values => {
    const createUser = onCreate ?? createUserApi
    const response = await createUser({ email: values.email, name: values.name })
    logger.info('User created successfully', { email: values.email })
    form.reset()
    onSuccess?.(response)
  })

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h3 className="text-2xl font-semibold text-slate-900 mb-6">新規ユーザー追加</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        {form.error && (
          <Alert variant="error" onDismiss={form.clearError}>
            {form.error}
          </Alert>
        )}
        <Input
          id="email"
          label="メールアドレス"
          type="email"
          value={form.fields.email.value}
          onChange={form.fields.email.onChange}
          error={form.fields.email.error}
          required
          placeholder="user@example.com"
          disabled={form.isSubmitting}
          fullWidth
        />
        <Input
          id="name"
          label="名前"
          type="text"
          value={form.fields.name.value}
          onChange={form.fields.name.onChange}
          error={form.fields.name.error}
          required
          placeholder="山田太郎"
          maxLength={100}
          disabled={form.isSubmitting}
          fullWidth
        />
        <div className="flex gap-3 justify-end pt-2">
          <Button type="button" onClick={onCancel} disabled={form.isSubmitting} variant="secondary">
            キャンセル
          </Button>
          <Button type="submit" disabled={form.isSubmitting} loading={form.isSubmitting}>
            {form.isSubmitting ? '作成中...' : '作成'}
          </Button>
        </div>
      </form>
    </div>
  )
}
