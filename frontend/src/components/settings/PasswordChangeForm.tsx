import { changePassword } from '@/lib/api/password'
import { logger } from '@/lib/logger'
import { Input, Button, Alert } from '@/components/ui'
import { useForm } from '@/hooks/useForm'
import { validators } from '@/lib/validation'

interface PasswordChangeFormProps {
  onSuccess: () => void
}

interface PasswordFormValues {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

export function PasswordChangeForm({ onSuccess }: PasswordChangeFormProps) {
  const form = useForm<PasswordFormValues>({
    fields: {
      currentPassword: {
        initialValue: '',
        validate: validators.required('現在のパスワードを入力してください'),
      },
      newPassword: {
        initialValue: '',
        validate: validators.compose(
          validators.required('新しいパスワードを入力してください'),
          validators.minLength(8, '新しいパスワードは8文字以上で入力してください')
        ),
      },
      confirmPassword: {
        initialValue: '',
        validate: validators.compose(
          validators.required('確認用パスワードを入力してください'),
          validators.match<PasswordFormValues>(
            'newPassword',
            '新しいパスワードと確認用パスワードが一致しません'
          )
        ),
      },
    },
    validate: values => {
      if (values.currentPassword === values.newPassword) {
        return '現在のパスワードと同じパスワードは使用できません'
      }
      return null
    },
    defaultErrorMessage: 'パスワードの変更に失敗しました',
    onSuccess: () => {
      logger.info('Password changed successfully')
      form.reset()
      onSuccess()
    },
  })

  const handleSubmit = form.handleSubmit(async values => {
    await changePassword({
      current_password: values.currentPassword,
      new_password: values.newPassword,
    })
  })

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h2 className="text-2xl font-semibold text-slate-900 mb-6">パスワード変更</h2>
      <form onSubmit={handleSubmit} className="space-y-4" aria-label="パスワード変更フォーム">
        {form.error && (
          <Alert variant="error" onDismiss={form.clearError}>
            {form.error}
          </Alert>
        )}

        <Input
          id="current-password"
          label="現在のパスワード"
          type="password"
          value={form.fields.currentPassword.value}
          onChange={form.fields.currentPassword.onChange}
          error={form.fields.currentPassword.error}
          disabled={form.isSubmitting}
          autoComplete="current-password"
          fullWidth
        />

        <Input
          id="new-password"
          label="新しいパスワード"
          type="password"
          value={form.fields.newPassword.value}
          onChange={form.fields.newPassword.onChange}
          error={form.fields.newPassword.error}
          disabled={form.isSubmitting}
          autoComplete="new-password"
          helperText="8文字以上で入力してください"
          fullWidth
        />

        <Input
          id="confirm-password"
          label="新しいパスワード（確認）"
          type="password"
          value={form.fields.confirmPassword.value}
          onChange={form.fields.confirmPassword.onChange}
          error={form.fields.confirmPassword.error}
          disabled={form.isSubmitting}
          autoComplete="new-password"
          fullWidth
        />

        <Button type="submit" disabled={form.isSubmitting} loading={form.isSubmitting} fullWidth>
          {form.isSubmitting ? '変更中...' : 'パスワードを変更'}
        </Button>
      </form>
    </div>
  )
}
