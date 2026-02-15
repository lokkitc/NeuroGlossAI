import { useExportMe } from '../../api/hooks'
import { Card } from '../../components/ui/Card/Card'
import { ErrorState } from '../../components/states/ErrorState/ErrorState'
import { LoadingState } from '../../components/states/LoadingState/LoadingState'
import { ui } from '../../styles/ui'
import styles from './DebugPage.module.css'

export function DebugPage() {
  const q = useExportMe()

  return (
    <Card title="Debug / Export">
      <div style={ui.rowWrap}>
        <button type="button" onClick={() => q.refetch()} disabled={q.isFetching}>
          {q.isFetching ? 'Обновляю…' : 'Обновить'}
        </button>
      </div>

      {q.isLoading ? <LoadingState title="Загружаю export…" /> : null}
      {q.error ? <ErrorState error={q.error} onRetry={() => q.refetch()} /> : null}

      {q.data ? <pre className={styles.pre}>{JSON.stringify(q.data, null, 2)}</pre> : null}
    </Card>
  )
}
