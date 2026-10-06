import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import Upload from './pages/Upload'
import Chat from './pages/Chat'
import Search from './pages/Search'
import DocViewer from './pages/DocViewer'
import ImageAnalysis from './pages/ImageAnalysis'
import Compare from './pages/Compare'
import Summarize from './pages/Summarize'
import Evaluation from './pages/Evaluation'
import Settings from './pages/Settings'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/search" element={<Search />} />
        <Route path="/documents/:id" element={<DocViewer />} />
        <Route path="/image-analysis" element={<ImageAnalysis />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/summarize" element={<Summarize />} />
        <Route path="/evaluation" element={<Evaluation />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}
