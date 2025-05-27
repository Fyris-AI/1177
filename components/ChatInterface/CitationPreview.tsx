import React, { useState, useRef } from "react";
import { Loader2, FileText } from "lucide-react";

interface CitationPreviewProps {
  url: string;
  className?: string;
}

const CitationPreview: React.FC<CitationPreviewProps> = ({
  url,
  className,
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const isPdf = url.toLowerCase().endsWith(".pdf");
  const domain = !isPdf && url ? new URL(url).hostname.replace("www.", "") : "";
  const proxyUrl = isPdf
    ? `/api/pdf/${encodeURIComponent(url)}`
    : `/api/proxy?url=${encodeURIComponent(url)}`;

  const handleIframeLoad = () => {
    setIsLoading(false);
  };

  const handleIframeError = () => {
    setIsLoading(false);
    setError(
      isPdf
        ? "Det gick inte att ladda PDF-filen."
        : "Det gick inte att ladda webbsidan."
    );
  };

  return (
    <div
      className={`rounded-md overflow-hidden w-full bg-card relative ${className}`}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-card/80 z-10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {error ? (
        <div className="absolute inset-0 flex items-center justify-center bg-card/80 z-10">
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      ) : (
        <iframe
          ref={iframeRef}
          src={proxyUrl}
          className="w-full h-full"
          title={isPdf ? "PDF Preview" : `Preview ${domain}`}
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          loading="lazy"
          sandbox={isPdf ? "" : "allow-scripts allow-same-origin"}
          referrerPolicy="no-referrer"
        />
      )}
    </div>
  );
};

export default CitationPreview;
