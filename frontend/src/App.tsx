import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import EC2Resources from "./pages/EC2Resources";
import S3Buckets from "./pages/S3Buckets";
import SecurityChecks from "./pages/SecurityChecks";
import ScanHistory from "./pages/ScanHistory";

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#0f172a",
            color: "#e2e8f0",
            border: "1px solid rgba(255,255,255,0.1)",
            fontSize: 13,
          },
        }}
      />
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="/ec2" element={<EC2Resources />} />
          <Route path="/s3" element={<S3Buckets />} />
          <Route path="/security" element={<SecurityChecks />} />
          <Route path="/scans" element={<ScanHistory />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
