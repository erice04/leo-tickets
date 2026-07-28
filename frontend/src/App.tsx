import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ThemeProvider } from "./theme/ThemeContext";
import { TicketPage } from "./pages/TicketPage";
import { ScannerPage } from "./pages/ScannerPage";
import { AdminPage } from "./pages/AdminPage";
import { DisplayEmailsPage } from "./pages/DisplayEmailsPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { DatabasePage } from "./pages/DatabasePage";

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
          <Route path="/admin/analytics" element={<AnalyticsPage />} />
          <Route path="/admin/database" element={<DatabasePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
