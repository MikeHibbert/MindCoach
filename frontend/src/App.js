import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ResponsiveLayout from './components/ResponsiveLayout';
import LoadingSpinner from './components/LoadingSpinner';

// Lazy load components for code splitting
const SubjectSelector = React.lazy(() => import('./components/SubjectSelector'));
const Survey = React.lazy(() => import('./components/Survey'));
const LessonViewer = React.lazy(() => import('./components/LessonViewer'));
const PaymentGate = React.lazy(() => import('./components/PaymentGate'));

function App() {
  return (
    <Router>
      <ResponsiveLayout>
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            <Route path="/" element={<SubjectSelector />} />
            <Route path="/subjects/:subject/survey" element={<Survey />} />
            <Route path="/subjects/:subject/lessons" element={<LessonViewer />} />
            <Route path="/subjects/:subject/lessons/:lessonId" element={<LessonViewer />} />
            <Route path="/payment/:subject" element={<PaymentGate />} />
          </Routes>
        </Suspense>
      </ResponsiveLayout>
    </Router>
  );
}

export default App;