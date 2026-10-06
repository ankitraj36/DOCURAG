import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, FileText, Upload, MessageSquare, Search,
  Image, GitCompare, FileBarChart, BarChart3, Settings, Sparkles
} from 'lucide-react'

const navItems = [
  { label: 'Core', items: [
    { to: '/dashboard', icon: LayoutDashboard, text: 'Dashboard' },
    { to: '/documents', icon: FileText, text: 'Documents' },
    { to: '/upload', icon: Upload, text: 'Upload' },
  ]},
  { label: 'AI Tools', items: [
    { to: '/chat', icon: MessageSquare, text: 'AI Chat' },
    { to: '/search', icon: Search, text: 'Search' },
    { to: '/image-analysis', icon: Image, text: 'Image Analysis' },
    { to: '/compare', icon: GitCompare, text: 'Compare' },
    { to: '/summarize', icon: FileBarChart, text: 'Summarize' },
  ]},
  { label: 'System', items: [
    { to: '/evaluation', icon: BarChart3, text: 'Evaluation' },
    { to: '/settings', icon: Settings, text: 'Settings' },
  ]},
]

export default function Layout() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon"><Sparkles size={18} /></div>
          <h1>DocuRAG</h1>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((section) => (
            <div key={section.label}>
              <div className="sidebar-section-label">{section.label}</div>
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
                >
                  <item.icon size={20} />
                  <span>{item.text}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div style={{ padding: '16px 12px', borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textAlign: 'center' }}>
            DocuRAG v1.0 · AI Document Intelligence
          </div>
        </div>
      </aside>
      <main className="main-content">
        <div className="page-container">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
