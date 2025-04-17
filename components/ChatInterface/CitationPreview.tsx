import React, { useState, useEffect } from "react";
import { ExternalLink, AlertCircle, Loader2, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

interface CitationPreviewProps {
  url: string;
}

const CitationPreview: React.FC<CitationPreviewProps> = ({ url }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [iframeKey, setIframeKey] = useState<number>(0); // Used to force iframe reload

  // Extract domain for display
  const domain = url ? new URL(url).hostname.replace("www.", "") : "";

  // Construct the proxy URL
  const proxyUrl = `/api/proxy?url=${encodeURIComponent(url)}`;

  // Reset loading state when URL changes
  useEffect(() => {
    setIsLoading(true);
    setError(null);
  }, [url]);

  const handleIframeLoad = () => {
    setIsLoading(false);
  };

  const handleIframeError = () => {
    setIsLoading(false);
    setError(
      "Det gick inte att ladda webbsidan. Försök igen eller klicka på 'Öppna' för att besöka sidan direkt."
    );
  };

  // Function to force reload the iframe
  const reloadIframe = () => {
    setIsLoading(true);
    setError(null);
    setIframeKey((prev) => prev + 1); // Change key to force React to recreate the iframe
  };

  return (
    <div className="flex flex-col gap-4 w-full">
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">{domain}</div>
        <div className="flex gap-2">
          {error && (
            <Button
              variant="outline"
              size="sm"
              onClick={reloadIframe}
              className="flex items-center gap-1"
            >
              <RefreshCcw className="h-3 w-3 mr-1" />
              Ladda om
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(url, "_blank")}
            className="flex items-center gap-1"
          >
            <ExternalLink className="h-3 w-3 mr-1" />
            Öppna
          </Button>
        </div>
      </div>

      <div className="border rounded-md overflow-hidden w-full bg-card relative">
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
          // Error state - show error and a thumbnail preview if possible
          <div className="p-4 flex flex-col gap-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4 mr-2" />
              <AlertTitle>Kunde inte ladda innehållet</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>

            {/* Fallback image - a screenshot of the site if available */}
            <div className="aspect-video bg-muted/50 rounded flex items-center justify-center">
              <img
                src={`https://api.microlink.io/?url=${encodeURIComponent(
                  url
                )}&screenshot=true&meta=false&embed=screenshot.url`}
                alt={`Förhandsgranskning av ${domain}`}
                className="max-w-full h-auto rounded"
                onError={(e) => {
                  // Hide the image if it fails to load
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            </div>
          </div>
        ) : (
          // TODO: We reach this point, but everything is still empty. We only see the website for a split second
          <iframe
            key={iframeKey}
            src={proxyUrl}
            className="w-full h-[60vh]"
            title="Citation preview"
            onLoad={handleIframeLoad}
            onError={handleIframeError}
            loading="lazy"
            sandbox="allow-scripts"
            referrerPolicy="no-referrer"
          ></iframe>
        )}
      </div>
    </div>
  );
};

export default CitationPreview;
