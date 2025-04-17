import React, { useState, useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";

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
  const [iframeKey, setIframeKey] = useState<number>(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const domain = url ? new URL(url).hostname.replace("www.", "") : "";
  const proxyUrl = `/api/proxy?url=${encodeURIComponent(url)}`;

  useEffect(() => {
    setIsLoading(true);
    setError(null);
  }, [url]);

  const handleIframeLoad = () => {
    setIsLoading(false);
    // Add padding to the iframe document when it loads
    const iframe = containerRef.current?.querySelector("iframe");
    if (iframe) {
      iframe.onload = () => {
        try {
          const iframeDoc =
            iframe.contentDocument || iframe.contentWindow?.document;
          if (iframeDoc) {
            iframeDoc.body.style.paddingBottom = "50px"; // Add space at bottom
          }
        } catch (e) {
          // Cross-origin error handling
          console.log("Couldn't access iframe document");
        }
      };
    }
  };

  const handleIframeError = () => {
    setIsLoading(false);
    setError(
      "Det gick inte att ladda webbsidan. Försök igen eller klicka på 'Öppna' för att besöka sidan direkt."
    );
  };

  return (
    <div
      className={`rounded-md overflow-hidden w-full bg-card relative ${className}`}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-card/80 z-10">
          <div className="flex flex-col items-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
            <span className="text-sm text-muted-foreground">
              Laddar innehåll...
            </span>
          </div>
        </div>
      )}

      {error ? (
        <p className="absolute inset-0 flex items-center justify-center bg-card/80 z-10">
          Kunde inte ladda sidan.
        </p>
      ) : (
        <div ref={containerRef} className="h-full mask-fade-out">
          <iframe
            key={iframeKey}
            src={proxyUrl}
            className="w-full h-full"
            title={`Förhandgranskning ${domain}`}
            onLoad={handleIframeLoad}
            onError={handleIframeError}
            loading="lazy"
            sandbox="allow-scripts allow-same-origin"
            referrerPolicy="no-referrer"
          />
        </div>
      )}
    </div>
  );
};

export default CitationPreview;
