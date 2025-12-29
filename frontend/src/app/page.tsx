"use client";
import React from "react";
import ArbTable, { Opportunity } from "@/components/ArbTable";
import ArbDetailModal from "@/components/ArbDetailModal";
import ThemeToggle from "@/components/ThemeToggle";
import ScanButton from "@/components/ScanButton";
import { fetchOpportunities, refreshArbitrage } from "@/lib/api";

export default function Home() {
  const [modalOpen, setModalOpen] = React.useState(false);
  const [selected, setSelected] = React.useState<Opportunity | null>(null);
  const [opportunities, setOpportunities] = React.useState<Opportunity[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Fetch opportunities on load
  React.useEffect(() => {
    loadOpportunities();
  }, []);

  const loadOpportunities = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOpportunities();
      setOpportunities(data);
    } catch (err: any) {
      setError(err?.message || "Failed to fetch opportunities");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (opp: Opportunity) => {
    setSelected(opp);
    setModalOpen(true);
  };

  const handleClose = () => {
    setModalOpen(false);
    setSelected(null);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    try {
      await refreshArbitrage();
      await loadOpportunities();
    } catch (err: any) {
      setError(err?.message || "Failed to refresh arbitrage");
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="flex w-full items-center justify-between px-8 py-6 border-b border-border bg-card/60">
        <h1 className="text-2xl font-bold tracking-tight">Kalshi vs Polymarket Arbitrage</h1>
        <div className="flex items-center gap-3">
          <ScanButton onScan={handleRefresh} loading={refreshing} buttonText="Refresh Opportunities" />
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto max-w-4xl p-8 flex flex-col gap-10">
        <div>
          <h2 className="text-lg font-semibold mb-4">Latest Opportunities</h2>
          {error && (
            <div className="mb-4 text-destructive">{error}</div>
          )}
          {loading ? (
            <div className="py-12 text-center text-muted-foreground animate-pulse">Loading opportunities...</div>
          ) : (
            <ArbTable opportunities={opportunities} onSelect={handleSelect} />
          )}
        </div>
      </main>
      <ArbDetailModal open={modalOpen} opportunity={selected} onClose={handleClose} />
    </div>
  );
}
