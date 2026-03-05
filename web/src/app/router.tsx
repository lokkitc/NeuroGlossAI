import { createBrowserRouter, Navigate } from 'react-router-dom'
import AppLayout from './shell/AppLayout'
import AuthLayout from './shell/AuthLayout'
import ProtectedRoute from './shell/ProtectedRoute'
import HomePage from '../pages/HomePage/HomePage'
import ChatPage from '../pages/ChatPage/ChatPage'
import CreateCharacterPage from '../pages/CreateCharacterPage/CreateCharacterPage'
import ProfilePage from '../pages/ProfilePage/ProfilePage'
import CharacterDetailPage from '../pages/CharacterDetailPage/CharacterDetailPage'
import LoginPage from '../pages/LoginPage/LoginPage'
import RegisterPage from '../pages/RegisterPage/RegisterPage'

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/characters/:characterId', element: <CharacterDetailPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          { path: '/chat', element: <ChatPage /> },
          { path: '/chat/:sessionId', element: <ChatPage /> },
          { path: '/characters/new', element: <CreateCharacterPage /> },
          { path: '/profile', element: <ProfilePage /> },
        ],
      },
    ],
  },
  {
    element: <AuthLayout />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
    ],
  },
  { path: '*', element: <Navigate to='/' replace /> },
])
