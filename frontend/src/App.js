import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ResponsiveLayout from './components/ResponsiveLayout';
import SubjectSelector from './components/SubjectSelector';
import Survey from './components/Survey';
import LessonViewer from './components/LessonViewer';
import PaymentGate from './components/PaymentGate';

function App() {
  return (
    <Router>
      <ResponsiveLayout>
        <Routes>
          <Route path="/" element={<SubjectSelector />} />
          <Route path="/subjects/:subject/survey" element={<Survey />} />
          <Route path="/subjects/:subject/lessons" element={<LessonViewer />} />
          <Route path="/subjects/:subject/lessons/:lessonId" element={<LessonViewer />} />
          <Route path="/payment/:subject" element={<PaymentGate />} />
        </Routes>
      </ResponsiveLayout>
    </Router>
  );
}

export default App;