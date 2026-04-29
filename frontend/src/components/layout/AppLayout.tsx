import { Outlet, useNavigate } from "react-router-dom";
import { useState } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

// Wraps every page with Sidebar + Topbar.
// `scanTick` is a poor-man's cache buster: every successful scan increments it,
// and pages re-fetch via React's `key` prop. Keeps the demo snappy.
export default function AppLayout() {
  const [scanTick, setScanTick] = useState(0);
  const navigate = useNavigate();

  const handleScanComplete = () => {
    setScanTick((t) => t + 1);
    navigate("/");
  };

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar onScanComplete={handleScanComplete} />
        <main key={scanTick} className="flex-1 p-4 md:p-8 max-w-[1600px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
