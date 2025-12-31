import type { UserCreateRequest, UserCreateResponse, UserRole } from '@/types/user'
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
  role: UserRole
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
      role: {
        initialValue: 'user' as UserRole,
      },
    },
    defaultErrorMessage: 'ユーザーの作成に失敗しました',
  })

  const handleSubmit = form.handleSubmit(async values => {
    const createUser = onCreate ?? createUserApi
    const response = await createUser({ email: values.email, name: values.name, role: values.role })
    logger.info('User created successfully', { email: values.email, role: values.role })
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
        <div className="w-full">
          <label htmlFor="role" className="block text-sm font-medium text-slate-700 mb-1">
            権限
            <span className="text-red-500 ml-1">*</span>
          </label>
          <select
            id="role"
            value={form.fields.role.value}
            onChange={e => form.fields.role.setValue(e.target.value as UserRole)}
            disabled={form.isSubmitting}
            className="block w-full px-3 py-2 border rounded-lg text-slate-900 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0 disabled:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-500 min-h-[2.75rem] border-slate-300 focus:border-blue-500 focus:ring-blue-200"
          >
            <option value="user">一般ユーザー</option>
            <option value="admin">管理者</option>
          </select>
        </div>
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
