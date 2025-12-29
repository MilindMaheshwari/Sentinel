import * as React from "react";
import { Dialog, DialogContent, DialogTitle, DialogDescription, DialogClose } from "@/components/ui/dialog";
import { Opportunity } from "./ArbTable";

interface ArbDetailModalProps {
  open: boolean;
  opportunity: Opportunity | null;
  onClose: () => void;
}

const ArbDetailModal: React.FC<ArbDetailModalProps> = ({ open, opportunity, onClose }) => {
  if (!opportunity) return null;
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogTitle>Opportunity Details</DialogTitle>
        <DialogDescription>
          <div className="space-y-2 py-2 text-sm">
            <div><span className="font-semibold">Market:</span> {opportunity.market}</div>
            <div><span className="font-semibold">Ticker:</span> {opportunity.ticker}</div>
            <div><span className="font-semibold">Price:</span> {opportunity.price}</div>
            <div><span className="font-semibold">Profit:</span> {opportunity.profit}</div>
            {opportunity.actionUrl && (
              <div>
                <span className="font-semibold">Trade Link:</span> {" "}
                <a href={opportunity.actionUrl} target="_blank" rel="noopener noreferrer" className="underline text-primary">Open</a>
              </div>
            )}
          </div>
        </DialogDescription>
        <DialogClose asChild>
          <button className="mt-4 w-full rounded bg-primary px-4 py-2 text-background hover:bg-primary/90">Close</button>
        </DialogClose>
      </DialogContent>
    </Dialog>
  );
};

export default ArbDetailModal;

