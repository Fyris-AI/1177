import React from "react";
import { Button } from "@/components/ui/button";
import { ExternalLink, FileText } from "lucide-react";
import { useConfig } from "@/contexts/ConfigContext";
import CitationPreview from "./CitationPreview";

interface CitationButtonProps {
  url: string;
  className?: string;
}

const CitationButton: React.FC<CitationButtonProps> = ({ url, className }) => {
  const { config } = useConfig();
  const isPdf = url.toLowerCase().endsWith(".pdf");
  const Icon = isPdf ? FileText : ExternalLink;

  if (config.openLinksInNewTab) {
    return (
      <Button
        variant="ghost"
        size="icon"
        className={className}
        onClick={() => window.open(url, "_blank", "noopener,noreferrer")}
        title={isPdf ? "Öppna PDF" : "Öppna länk i ny flik"}
      >
        <Icon className="h-4 w-4" />
      </Button>
    );
  }

  return (
    <div className="relative">
      <CitationPreview url={url} className={className} />
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-2 right-2 z-20"
        title={isPdf ? "Öppna PDF" : "Öppna länk i ny flik"}
        onClick={() => window.open(url, "_blank", "noopener,noreferrer")}
      >
        <Icon className="h-4 w-4" />
      </Button>
    </div>
  );
};

export default CitationButton;
