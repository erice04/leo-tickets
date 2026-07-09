import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ThemeProvider } from "./theme/ThemeContext";
import { TicketPage } from "./pages/TicketPage";
import { ScannerPage } from "./pages/ScannerPage";
import { AdminPage } from "./pages/AdminPage";
import { DisplayEmailsPage } from "./pages/DisplayEmailsPage";
import { DisplayLogPage } from "./pages/DisplayLogPage";

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<TicketPage />} />
          <Route path="/scanner" element={<ScannerPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/admin/display" element={<DisplayEmailsPage mode="guest" />} />
          <Route
            path="/admin/blacklist/display"
            element={<DisplayEmailsPage mode="blacklist" />}
          />
          <Route path="/admin/log" element={<DisplayLogPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
