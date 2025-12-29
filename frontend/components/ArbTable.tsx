import React from "react";

// Type definition for a single opportunity row
export type Opportunity = {
  id: string;
  market: string;
  ticker: string;
  price: string;
  profit: string;
  actionUrl?: string; // optional external link
};

interface ArbTableProps {
  opportunities: Opportunity[];
  onSelect: (opp: Opportunity) => void;
}

const ArbTable: React.FC<ArbTableProps> = ({ opportunities, onSelect }) => {
  return (
    <div className="relative w-full overflow-x-auto rounded-lg border border-muted bg-background shadow-sm dark:border-zinc-800">
      <table className="w-full min-w-[650px] text-sm text-left">
        <thead className="bg-muted dark:bg-zinc-900">
          <tr>
            <th className="px-5 py-3">Market</th>
            <th className="px-5 py-3">Ticker</th>
            <th className="px-5 py-3">Price</th>
            <th className="px-5 py-3">Profit</th>
            <th className="px-5 py-3">Action</th>
          </tr>
        </thead>
        <tbody>
          {opportunities.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">
                No opportunities at the moment.
              </td>
            </tr>
          ) : (
            opportunities.map((opp) => (
              <tr key={opp.id} className="hover:bg-accent/20 cursor-pointer" onClick={() => onSelect(opp)}>
                <td className="px-5 py-3 font-medium">{opp.market}</td>
                <td className="px-5 py-3">{opp.ticker}</td>
                <td className="px-5 py-3">{opp.price}</td>
                <td className="px-5 py-3">{opp.profit}</td>
                <td className="px-5 py-3">
                  {opp.actionUrl ? (
                    <a
                      href={opp.actionUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                      onClick={e => e.stopPropagation()}
                    >
                      Trade
                    </a>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default ArbTable;

