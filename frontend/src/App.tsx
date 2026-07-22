import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute, { AdminRoute } from './components/ProtectedRoute';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import IOCsPage from './pages/IOCsPage';
import VulnerabilitiesPage from './pages/VulnerabilitiesPage';
import PlaybooksPage from './pages/PlaybooksPage';
import UsersPage from './pages/UsersPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/iocs" element={<IOCsPage />} />
              <Route path="/vulnerabilities" element={<VulnerabilitiesPage />} />
              <Route path="/playbooks" element={<PlaybooksPage />} />
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <UsersPage />
                  </AdminRoute>
                }
              />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
