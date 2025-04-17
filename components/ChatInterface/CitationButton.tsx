import React from "react";
import { Button } from "@/components/ui/button";
import { BookOpen } from "lucide-react";

interface CitationButtonProps {
  link: string;
  name: string;
  onClick: (link: string) => void;
}

const CitationButton: React.FC<CitationButtonProps> = ({
  link,
  name,
  onClick,
}) => {
  return (
    <Button
      variant="link"
      size="sm" // Use a smaller size for compactness
      className="h-auto px-1 py-0.5 text-muted-foreground hover:text-primary" // Adjust padding and styling
      onClick={() => onClick(link)}
    >
      <BookOpen className="h-3 w-3 mr-1" /> {/* Add margin-right */}
      {name}
    </Button>
  );
};

CitationButton.displayName = "CitationButton";

export default CitationButton;
