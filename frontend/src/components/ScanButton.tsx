import * as React from "react";

interface ScanButtonProps {
  onScan: () => void;
  loading: boolean;
  buttonText?: string;
}

const ScanButton: React.FC<ScanButtonProps> = ({ onScan, loading, buttonText }) => (
  <button
    className="rounded bg-primary px-4 py-2 text-background font-semibold shadow transition-colors hover:bg-primary/90 disabled:opacity-50"
    onClick={onScan}
    disabled={loading}
  >
    {loading ? "Refreshing..." : buttonText || "Refresh Opportunities"}
  </button>
);

export default ScanButton;
