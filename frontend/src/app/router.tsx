import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '../components/AppLayout/AppLayout'
import { AuthLayout } from '../components/AuthLayout/AuthLayout'
import { ProtectedRoute } from '../components/ProtectedRoute/ProtectedRoute'
import { PublicRoute } from '../components/PublicRoute/PublicRoute'
import { CoursePage } from '../pages/CoursePage/CoursePage'
import { DebugPage } from '../pages/DebugPage/DebugPage'
import { LessonDetailPage } from '../pages/LessonDetailPage/LessonDetailPage'
import { LessonsPage } from '../pages/LessonsPage/LessonsPage'
import { LoginPage } from '../pages/LoginPage/LoginPage'
import { RegisterPage } from '../pages/RegisterPage/RegisterPage'
import { ReviewPage } from '../pages/ReviewPage/ReviewPage'
import { RoleplayPage } from '../pages/RoleplayPage/RoleplayPage'
import { SettingsPage } from '../pages/SettingsPage/SettingsPage'

export function AppRouter() {
  return (
    <Routes>
      <Route element={<PublicRoute />}>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/course" replace />} />
          <Route path="/course" element={<CoursePage />} />
          <Route path="/lessons" element={<LessonsPage />} />
          <Route path="/lessons/:id" element={<LessonDetailPage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/roleplay" element={<RoleplayPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/debug" element={<DebugPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
