import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import Cases from "@/pages/Cases";
import CaseDetail from "@/pages/CaseDetail";
import Templates from "@/pages/Templates";
import Mail from "@/pages/Mail";
import { AppShell } from "@/components/AppShell";

export default function App() {
  return (
    <Router>
      <AppShell>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/mail" element={<Mail />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/cases/:id" element={<CaseDetail />} />
          <Route path="/templates" element={<Templates />} />
        </Routes>
      </AppShell>
    </Router>
  );
}
