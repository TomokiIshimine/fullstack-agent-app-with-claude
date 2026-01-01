import { useEffect } from 'react'
import type { User } from '@/types/auth'
import { updateProfile } from '@/lib/api/profile'
import { logger } from '@/lib/logger'
import { Input, Button, Alert, Card } from '@/components/ui'
import { useForm } from '@/hooks/useForm'
import { validators } from '@/lib/validation'

interface ProfileUpdateFormProps {
  user: User | null
  onSuccess: (user: User) => void
}

interface ProfileFormValues {
  email: string
  name: string
}

export function ProfileUpdateForm({ user, onSuccess }: ProfileUpdateFormProps) {
  const form = useForm<ProfileFormValues>({
    fields: {
      email: {
        initialValue: user?.email ?? '',
        validate: validators.compose(
          validators.required('メールアドレスを入力してください'),
          validators.email('メールアドレスの形式が正しくありません')
        ),
      },
      name: {
        initialValue: user?.name ?? '',
        validate: validators.required('名前を入力してください'),
      },
    },
    defaultErrorMessage: 'プロフィールの更新に失敗しました',
  })

  // Sync form values when user prop changes
  useEffect(() => {
    if (user) {
      form.setInitialValues({
        email: user.email,
        name: user.name ?? '',
      })
    }
  }, [user?.email, user?.name, form.setInitialValues])

  const handleSubmit = form.handleSubmit(async values => {
    if (!user) {
      form.setError('ユーザー情報を取得できませんでした')
      return
    }

    const updatedUser = await updateProfile({
      email: values.email.trim(),
      name: values.name.trim(),
    })
    logger.info('Profile updated successfully', {
      userId: updatedUser.id,
      email: updatedUser.email,
    })
    onSuccess(updatedUser)
  })

  return (
    <Card>
      <h2 className="text-2xl font-semibold text-slate-900 mb-6">プロフィール</h2>
      <form className="space-y-4" onSubmit={handleSubmit} aria-label="プロフィール更新フォーム">
        {form.error && (
          <Alert variant="error" onDismiss={form.clearError}>
            {form.error}
          </Alert>
        )}

        <Input
          id="profile-name"
          label="名前"
          type="text"
          value={form.fields.name.value}
          onChange={form.fields.name.onChange}
          error={form.fields.name.error}
          disabled={form.isSubmitting}
          autoComplete="name"
          fullWidth
        />

        <Input
          id="profile-email"
          label="メールアドレス"
          type="email"
          value={form.fields.email.value}
          onChange={form.fields.email.onChange}
          error={form.fields.email.error}
          disabled={form.isSubmitting}
          autoComplete="email"
          helperText="ログインに使用するメールアドレスを設定します"
          fullWidth
        />

        <Button type="submit" disabled={form.isSubmitting} loading={form.isSubmitting} fullWidth>
          {form.isSubmitting ? '保存中...' : '変更を保存'}
        </Button>
      </form>
    </Card>
  )
}
