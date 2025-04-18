import React from "react";
import { Button } from "@/components/ui/button";
import { BookOpen, ExternalLink } from "lucide-react";

interface CitationButtonProps {
  link: string;
  name: string;
  onClick: (link: string) => void;
}

// Get variant from .env with Variant 1 as default
const CITATION_PREVIEW_IFRAME =
  process.env.NEXT_PUBLIC_CITATION_PREVIEW_IFRAME !== "false";

const CitationButton: React.FC<CitationButtonProps> = ({
  link,
  name,
  onClick,
}) => {
  return CITATION_PREVIEW_IFRAME ? (
    // Variant 1: Using the BookOpen icon to open CitationPreview
    <Button
      variant="link"
      size="sm"
      className="h-auto px-1 py-0.5 text-muted-foreground hover:text-primary"
      onClick={() => onClick(link)}
    >
      <BookOpen className="h-3 w-3 mr-1" />
      {name}
    </Button>
  ) : (
    // Variant 2: Using the ExternalLink icon to open the link directly
    <Button
      variant="link"
      size="sm"
      className="h-auto px-1 py-0.5 text-muted-foreground hover:text-primary"
      onClick={() => window.open(link, "_blank")}
    >
      <ExternalLink className="h-3 w-3 mr-1" />
      {name}
    </Button>
  );
};

CitationButton.displayName = "CitationButton";

export default CitationButton;
