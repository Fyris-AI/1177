import React from "react";
import { Button } from "@/components/ui/button";
import { BookOpen, ExternalLink } from "lucide-react";

interface CitationButtonProps {
  url: string;
  name: string;
  onPreview: (url: string) => void;
}

// Get variant from .env with Variant 1 as default
const CITATION_PREVIEW_IFRAME =
  process.env.NEXT_PUBLIC_CITATION_PREVIEW_IFRAME !== "false";

const CitationButton: React.FC<CitationButtonProps> = ({
  url,
  name,
  onPreview,
}) => {
  if (!url) return null;

  // Extract just the filename from the path if it's a full path
  const filename = url.split("/").pop() || url;

  // Construct the PDF preview URL - just use the filename directly
  const pdfUrl = filename;

  return CITATION_PREVIEW_IFRAME ? (
    // Variant 1: Using the BookOpen icon to open CitationPreview
    <Button
      variant="link"
      size="sm"
      className="h-auto px-1 py-0.5 text-muted-foreground hover:text-primary"
      onClick={() => onPreview(pdfUrl)}
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
      onClick={() => window.open(pdfUrl, "_blank")}
    >
      <ExternalLink className="h-3 w-3 mr-1" />
      {name}
    </Button>
  );
};

CitationButton.displayName = "CitationButton";

export default CitationButton;
