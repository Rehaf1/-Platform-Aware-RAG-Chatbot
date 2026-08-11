import { useState } from "react"
import Sidebar from "./components/Sidebar"
import UploadPanel from "./components/UploadPanel"
import DocumentTable from "./components/DocumentTable"
import UnansweredQuestions from "./components/UnansweredQuestions"
import FrequentlyAsked from "./components/FrequentlyAsked"

export default function App() {
  const [active, setActive] = useState("documents")
  const [refreshSignal, setRefreshSignal] = useState(0)

  return (
    <div className="flex min-h-screen">
      <Sidebar active={active} onNavigate={setActive} />

      <main className="flex-1 px-12 py-10 max-w-5xl">
        {active === "documents" && (
          <>
            <h1 className="font-display text-2xl font-bold mb-1.5">Documents</h1>
            <p className="text-sm text-muted mb-6">
              Upload documents to the knowledge base and manage what's already indexed.
            </p>
            <UploadPanel onUploaded={() => setRefreshSignal((n) => n + 1)} />
            <div className="mt-8">
              <DocumentTable refreshSignal={refreshSignal} />
            </div>
          </>
        )}

        {active === "unanswered" && <UnansweredQuestions />}
        {active === "faq" && <FrequentlyAsked />}
      </main>
    </div>
  )
}
