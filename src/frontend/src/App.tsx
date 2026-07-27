import { Route, Routes, Navigate } from 'react-router-dom'
import { SessionProvider } from './context/SessionContext.tsx'
import JoinSession from './screens/JoinSession.tsx'
import CreateSession from './screens/CreateSession.tsx'
import Lobby from './screens/Lobby.tsx'
import RoleBriefing from './screens/RoleBriefing.tsx'
import ActiveWorkspace from './screens/ActiveWorkspace.tsx'
import InjectDetail from './screens/InjectDetail.tsx'
import DecisionSubmission from './screens/DecisionSubmission.tsx'
import Completion from './screens/Completion.tsx'

export default function App() {
  return (
    <SessionProvider>
      <Routes>
        <Route path="/" element={<Navigate to="/join" replace />} />
        <Route path="/join" element={<JoinSession />} />
        <Route path="/create" element={<CreateSession />} />
        <Route path="/sessions/:sessionId/lobby" element={<Lobby />} />
        <Route path="/sessions/:sessionId/briefing" element={<RoleBriefing />} />
        <Route path="/sessions/:sessionId/workspace" element={<ActiveWorkspace />} />
        <Route path="/sessions/:sessionId/workspace/injects/:injectId" element={<InjectDetail />} />
        <Route path="/sessions/:sessionId/workspace/injects/:injectId/decision" element={<DecisionSubmission />} />
        <Route path="/sessions/:sessionId/completion" element={<Completion />} />
      </Routes>
    </SessionProvider>
  )
}
