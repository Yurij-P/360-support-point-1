import { createContext, useContext, useState, type ReactNode } from 'react'

interface SessionState {
  sessionId: string | null
  participantToken: string | null
  facilitatorToken: string | null
  setSession: (sessionId: string, participantToken: string) => void
  setFacilitator: (sessionId: string, facilitatorToken: string) => void
  clearSession: () => void
}

const SessionContext = createContext<SessionState | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [participantToken, setParticipantToken] = useState<string | null>(null)
  const [facilitatorToken, setFacilitatorToken] = useState<string | null>(null)

  function setSession(id: string, token: string) {
    setSessionId(id)
    setParticipantToken(token)
    setFacilitatorToken(null)
  }

  function setFacilitator(id: string, token: string) {
    setSessionId(id)
    setFacilitatorToken(token)
    setParticipantToken(null)
  }

  function clearSession() {
    setSessionId(null)
    setParticipantToken(null)
    setFacilitatorToken(null)
  }

  return (
    <SessionContext.Provider value={{ sessionId, participantToken, facilitatorToken, setSession, setFacilitator, clearSession }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession(): SessionState {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used inside <SessionProvider>')
  return ctx
}
