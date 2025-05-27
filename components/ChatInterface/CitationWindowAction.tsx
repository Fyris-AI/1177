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
  const getPdfUrl = (filename: string) => {
    if (filename.startsWith("/api/pdf/")) {
      return filename;
    }
    return `/api/pdf/${encodeURIComponent(filename)}`;
  };

  const handleOpenInNewTab = () => {
    if (!citationUrl) return;

    const isPdf = citationUrl.toLowerCase().endsWith(".pdf");
    const url = isPdf ? getPdfUrl(citationUrl) : citationUrl;
    window.open(url, "_blank");
  };

  return (
    <div className={`flex gap-2 w-full ${className}`}>
      <Button
        variant="secondary"
        onClick={handleOpenInNewTab}
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
