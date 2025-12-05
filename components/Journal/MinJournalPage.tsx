"use client";

import React from 'react';
import { useAuth, PatientJournalData } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { ArrowLeft, User, Activity, Heart, Brain, Bone, LogOut } from 'lucide-react';

interface MinJournalPageProps {
  onBack: () => void;
}

function LabResultsTable({ title, data }: { title: string; data: Record<string, string | number> | undefined }) {
  if (!data || Object.keys(data).length === 0) return null;
  
  return (
    <div className="mb-4">
      <h4 className="font-medium text-sm text-muted-foreground mb-2">{title}</h4>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="bg-muted/50 rounded-lg p-2">
            <span className="text-xs text-muted-foreground block">{key.replace(/_/g, ' ')}</span>
            <span className="font-medium text-sm">{String(value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function JournalSection({ 
  title, 
  icon: Icon, 
  children 
}: { 
  title: string; 
  icon: React.ComponentType<{ className?: string }>; 
  children: React.ReactNode;
}) {
  return (
    <div className="bg-card rounded-xl border border-border p-4 sm:p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <h3 className="text-lg font-semibold text-title">{title}</h3>
      </div>
      {children}
    </div>
  );
}

export function MinJournalPage({ onBack }: MinJournalPageProps) {
  const { user, journalData, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user || !journalData) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Ingen journaldata tillgänglig.</p>
      </div>
    );
  }

  const data = journalData.labs_and_exams;

  const handleLogout = () => {
    logout();
    onBack();
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="sticky top-0 z-10 flex items-center justify-between p-4 border-b border-border bg-background">
        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Tillbaka till chatten
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleLogout}
          className="flex items-center gap-2"
        >
          <LogOut className="h-4 w-4" />
          Logga ut
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-4 sm:p-6 space-y-6">
          {/* User info header */}
          <div className="bg-gradient-to-r from-primary/10 to-primary/5 rounded-xl p-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                <User className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-title">Min Journal</h1>
                <p className="text-muted-foreground">{user.name}</p>
                <p className="text-sm text-muted-foreground">
                  Personnummer: {user.personnummer.replace(/(\d{8})(\d{4})/, '$1-$2')}
                </p>
              </div>
            </div>
          </div>

          {/* Current status */}
          {data.current && (
            <JournalSection title="Senase värden" icon={Activity}>
              <LabResultsTable title="Labvärden" data={data.current.labs} />
              {data.current.ekg && (
                <div className="mt-3 p-3 bg-muted/50 rounded-lg">
                  <span className="text-xs text-muted-foreground block">EKG</span>
                  <span className="text-sm">{data.current.ekg}</span>
                </div>
              )}
              {data.current.lungröntgen && (
                <div className="mt-2 p-3 bg-muted/50 rounded-lg">
                  <span className="text-xs text-muted-foreground block">Lungröntgen</span>
                  <span className="text-sm">{data.current.lungröntgen}</span>
                </div>
              )}
              {data.current.eko && (
                <div className="mt-2 p-3 bg-muted/50 rounded-lg">
                  <span className="text-xs text-muted-foreground block">Ekokardiografi</span>
                  <span className="text-sm">{data.current.eko}</span>
                </div>
              )}
            </JournalSection>
          )}

          {/* Cardiometabolic history */}
          {data.cardiometabolic && (
            <JournalSection title="Hjärt-kärl och metabolism" icon={Heart}>
              {Object.entries(data.cardiometabolic).map(([period, values]) => (
                <LabResultsTable 
                  key={period} 
                  title={period.replace(/_/g, ' ')} 
                  data={values as Record<string, string | number>} 
                />
              ))}
            </JournalSection>
          )}

          {/* Cognitive assessment */}
          {data.cognitive && (
            <JournalSection title="Kognitiv bedömning" icon={Brain}>
              <LabResultsTable title="Labvärden" data={data.cognitive.labs} />
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                {data.cognitive.MMT !== undefined && (
                  <div className="p-3 bg-muted/50 rounded-lg">
                    <span className="text-xs text-muted-foreground block">MMT</span>
                    <span className="font-medium">{data.cognitive.MMT}/30</span>
                  </div>
                )}
                {data.cognitive.clock_test && (
                  <div className="p-3 bg-muted/50 rounded-lg">
                    <span className="text-xs text-muted-foreground block">Klocktest</span>
                    <span className="text-sm">{data.cognitive.clock_test}</span>
                  </div>
                )}
                {data.cognitive.MRT && (
                  <div className="p-3 bg-muted/50 rounded-lg">
                    <span className="text-xs text-muted-foreground block">MRT</span>
                    <span className="text-sm">{data.cognitive.MRT}</span>
                  </div>
                )}
              </div>
            </JournalSection>
          )}

          {/* Orthopedics */}
          {(data.youth?.imaging || data.knee_arthrosis_period) && (
            <JournalSection title="Ortopedi" icon={Bone}>
              {data.youth?.imaging && (
                <div className="space-y-2 mb-4">
                  <h4 className="font-medium text-sm text-muted-foreground">Ungdomsfrakturer</h4>
                  {Object.entries(data.youth.imaging).map(([key, value]) => (
                    <div key={key} className="p-3 bg-muted/50 rounded-lg">
                      <span className="text-xs text-muted-foreground block">
                        {key.replace(/_/g, ' ').replace(/(\d+)/, ' ($1 år)')}
                      </span>
                      <span className="text-sm">{value}</span>
                    </div>
                  ))}
                </div>
              )}
              {data.knee_arthrosis_period && (
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-muted-foreground">Knäartros</h4>
                  {data.knee_arthrosis_period.xray && (
                    <div className="p-3 bg-muted/50 rounded-lg">
                      <span className="text-xs text-muted-foreground block">Röntgen</span>
                      <span className="text-sm">{data.knee_arthrosis_period.xray}</span>
                    </div>
                  )}
                  {data.knee_arthrosis_period.postop && (
                    <div className="p-3 bg-muted/50 rounded-lg">
                      <span className="text-xs text-muted-foreground block">Postoperativ</span>
                      <span className="text-sm">{data.knee_arthrosis_period.postop}</span>
                    </div>
                  )}
                </div>
              )}
            </JournalSection>
          )}

          {/* Urology */}
          {data.urology && (
            <JournalSection title="Urologi" icon={Activity}>
              {data.urology.PSA_trend && (
                <div className="mb-3 p-3 bg-muted/50 rounded-lg">
                  <span className="text-xs text-muted-foreground block">PSA-trend</span>
                  <span className="text-sm">{data.urology.PSA_trend.join(' → ')}</span>
                </div>
              )}
              {data.urology.urine && (
                <div className="mb-2 p-3 bg-muted/50 rounded-lg">
                  <span className="text-xs text-muted-foreground block">Urinprov</span>
                  <span className="text-sm">{data.urology.urine}</span>
                </div>
              )}
              {data.urology.ultrasound && (
                <div className="p-3 bg-muted/50 rounded-lg">
                  <span className="text-xs text-muted-foreground block">Ultraljud</span>
                  <span className="text-sm">{data.urology.ultrasound}</span>
                </div>
              )}
            </JournalSection>
          )}

          {/* Historical lab values */}
          {(data.youth?.labs || data.adult?.labs_initial) && (
            <JournalSection title="Historiska labvärden" icon={Activity}>
              <LabResultsTable title="Ungdom" data={data.youth?.labs} />
              <LabResultsTable title="Vuxen (initial)" data={data.adult?.labs_initial} />
              {data.adult?.ekg && (
                <div className="mt-2 p-3 bg-muted/50 rounded-lg">
                  <span className="text-xs text-muted-foreground block">EKG (vuxen)</span>
                  <span className="text-sm">{data.adult.ekg}</span>
                </div>
              )}
            </JournalSection>
          )}

          {/* Footer spacing */}
          <div className="h-8" />
        </div>
      </div>
    </div>
  );
}

