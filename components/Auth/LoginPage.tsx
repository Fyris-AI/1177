"use client";

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ArrowLeft, Shield, Loader2 } from 'lucide-react';

interface LoginPageProps {
  onBack: () => void;
  onLoginSuccess: () => void;
}

export function LoginPage({ onBack, onLoginSuccess }: LoginPageProps) {
  const { login, isLoading } = useAuth();
  const [personnummer, setPersonnummer] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Basic validation
    const cleanedPnr = personnummer.replace(/[-\s]/g, '');
    if (cleanedPnr.length !== 12 && cleanedPnr.length !== 10) {
      setError('Ange ett giltigt personnummer (YYYYMMDDXXXX)');
      return;
    }

    const success = await login(personnummer);
    if (success) {
      onLoginSuccess();
    } else {
      setError('Inloggningen misslyckades. Försök igen.');
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header with back button */}
      <div className="flex items-center p-4 border-b border-border">
        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Tillbaka
        </Button>
      </div>

      {/* Login form */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md space-y-8">
          {/* Header */}
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
              <Shield className="h-8 w-8 text-primary" />
            </div>
            <h1 className="text-2xl font-bold text-title">Logga in</h1>
            <p className="mt-2 text-muted-foreground">
              Logga in för att se din journal och få personliga svar
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="personnummer">Personnummer</Label>
              <Input
                id="personnummer"
                type="text"
                placeholder="YYYYMMDDXXXX"
                value={personnummer}
                onChange={(e) => setPersonnummer(e.target.value)}
                className="text-lg"
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                Ange ditt personnummer för att logga in med BankID
              </p>
            </div>

            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={isLoading || !personnummer}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loggar in...
                </>
              ) : (
                'Logga in med BankID'
              )}
            </Button>
          </form>

          {/* Demo notice */}
          <div className="mt-6 p-4 bg-muted rounded-lg">
            <p className="text-xs text-center text-muted-foreground">
              <strong>Demo:</strong> Detta är en demonstration. Ange valfritt personnummer för att testa inloggningen.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

