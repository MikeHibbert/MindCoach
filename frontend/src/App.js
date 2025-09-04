import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ResponsiveLayout from './components/ResponsiveLayout';
import LoadingSpinner from './components/LoadingSpinner';

// Lazy load components for code splitting
const SubjectSelector = React.lazy(() => import('./components/SubjectSelector'));
const SurveyContainer = React.lazy(() => import('./components/SurveyContainer'));
const SurveyResults = React.lazy(() => import('./components/SurveyResults'));
const LessonViewer = React.lazy(() => import('./components/LessonViewer'));
const RAGDocumentManager = React.lazy(() => import('./components/RAGDocumentManager'));
const ErrorBoundary = React.lazy(() => import('./components/ErrorBoundary'));

function App() {
  return (
    <AuthProvider>
      <Router>
        <ResponsiveLayout>
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route path="/" element={<SubjectSelector />} />
              {/* Anonymous user routes */}
              <Route path="/subjects/:subject/survey" element={
                <ErrorBoundary>
                  <SurveyContainer />
                </ErrorBoundary>
              } />
              <Route path="/subjects/:subject/results" element={<SurveyResults />} />
              <Route path="/subjects/:subject/lessons" element={<LessonViewer />} />
              <Route path="/subjects/:subject/lessons/:lessonId" element={<LessonViewer />} />
              {/* Authenticated user routes */}
              <Route path="/users/:userId/subjects/:subject/survey" element={
                <ErrorBoundary>
                  <SurveyContainer />
                </ErrorBoundary>
              } />
              <Route path="/users/:userId/subjects/:subject/results" element={<SurveyResults />} />
              <Route path="/users/:userId/subjects/:subject/lessons" element={<LessonViewer />} />
              <Route path="/users/:userId/subjects/:subject/lessons/:lessonId" element={<LessonViewer />} />
              <Route path="/admin/rag-documents" element={<RAGDocumentManager />} />
            </Routes>
          </Suspense>
        </ResponsiveLayout>
      </Router>
    </AuthProvider>
  );
}

export default App;