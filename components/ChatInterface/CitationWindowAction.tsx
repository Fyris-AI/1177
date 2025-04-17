import { Button } from "@/components/ui/button";

interface CitationActionsProps {
  citationUrl?: string | null;
  onClose: () => void;
  className?: string;
}

export function CitationWindowActions({
  citationUrl,
  onClose,
  className,
}: CitationActionsProps) {
  return (
    <div className={`flex gap-2 w-full ${className}`}>
      <Button
        variant="secondary"
        onClick={() => window.open(citationUrl || "", "_blank")}
        className="w-full h-8"
        disabled={!citationUrl}
      >
        Öppna i ny flik
      </Button>
      <Button variant="primary" onClick={onClose} className="w-[20vh] h-8">
        Stäng
      </Button>
    </div>
  );
}
