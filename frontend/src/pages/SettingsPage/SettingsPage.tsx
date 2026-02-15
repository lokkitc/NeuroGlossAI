import { useEffect, useMemo, useState } from 'react'
import { usersApi } from '../../api/users'
import { useExportMe, useResetMe } from '../../api/hooks'
import { Card } from '../../components/ui/Card/Card'
import { ErrorState } from '../../components/states/ErrorState/ErrorState'
import { useAuthStore } from '../../stores/authStore'
import { ui } from '../../styles/ui'
import styles from './SettingsPage.module.css'

function parseCsv(value: string): string[] {
  return value
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

export function SettingsPage() {
  const me = useAuthStore((s) => s.me)
  const loadMe = useAuthStore((s) => s.loadMe)

  const [nativeLanguage, setNativeLanguage] = useState(me?.native_language ?? '')
  const [targetLanguage, setTargetLanguage] = useState(me?.target_language ?? '')
  const [interestsCsv, setInterestsCsv] = useState((me?.interests ?? []).join(', '))

  useEffect(() => {
    if (!me) return
    setNativeLanguage(me.native_language ?? '')
    setTargetLanguage(me.target_language ?? '')
    setInterestsCsv((me.interests ?? []).join(', '))
  }, [me])

  const interests = useMemo(() => parseCsv(interestsCsv), [interestsCsv])

  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<unknown>(null)

  const exportQ = useExportMe()
  const resetM = useResetMe()

  const onSave = async () => {
    setIsSaving(true)
    setSaveError(null)
    try {
      if (nativeLanguage && targetLanguage) {
        await usersApi.updateLanguages({ native_language: nativeLanguage, target_language: targetLanguage })
      }
      await usersApi.patchMe({ interests })
      await loadMe()
    } catch (e) {
      setSaveError(e)
    } finally {
      setIsSaving(false)
    }
  }

  const onReset = async () => {
    if (!window.confirm('Сбросить контент пользователя? Будут удалены курс/прогресс/уроки/словарь.')) return
    await resetM.mutateAsync()
    await loadMe()
  }

  return (
    <div className={styles.grid}>
      <Card title="Профиль">
        <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
          <div style={ui.text.muted}>
            {me ? `${me.username} · ${me.email} · ${me.xp} XP` : '…'}
          </div>

          <label>
            Родной язык
            <input value={nativeLanguage} onChange={(e) => setNativeLanguage(e.target.value)} placeholder="Russian" />
          </label>
          <label>
            Целевой язык
            <input value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)} placeholder="English" />
          </label>
          <label>
            Интересы (через запятую)
            <input value={interestsCsv} onChange={(e) => setInterestsCsv(e.target.value)} placeholder="Travel, Music" />
          </label>

          <div className={styles.actions}>
            <button type="button" onClick={onSave} disabled={isSaving}>
              {isSaving ? 'Сохраняю…' : 'Сохранить'}
            </button>
            <button type="button" onClick={() => loadMe()} disabled={isSaving}>
              Обновить профиль
            </button>
          </div>

          {saveError ? <ErrorState error={saveError} title="Ошибка сохранения" /> : null}
        </form>
      </Card>

      <Card title="Данные">
        <div className={styles.form}>
          <button type="button" onClick={() => exportQ.refetch()} disabled={exportQ.isFetching}>
            {exportQ.isFetching ? 'Готовлю…' : 'Экспорт (JSON)'}
          </button>
          {exportQ.error ? <ErrorState error={exportQ.error} title="Ошибка экспорта" /> : null}

          <button type="button" onClick={onReset} disabled={resetM.isPending}>
            {resetM.isPending ? 'Сбрасываю…' : 'Сбросить контент'}
          </button>
          {resetM.error ? <ErrorState error={resetM.error} title="Ошибка сброса" /> : null}

          <div style={ui.text.mutedOnly}>
            Экспорт откроется на странице Debug (там удобно копировать).
          </div>
        </div>
      </Card>
    </div>
  )
}
