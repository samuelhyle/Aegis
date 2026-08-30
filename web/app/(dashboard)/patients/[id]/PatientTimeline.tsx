"use client";

import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ScrollArea } from "@/components/ui/ScrollArea";
import { cn, formatDateTime } from "@/lib/utils";
import { Circle, HeartPulse, Pill, FlaskConical, Calendar } from "lucide-react";
import type { Condition, Medication, Observation, Encounter } from "@/types";

interface TimelineEvent {
  id: string;
  type: "condition" | "medication" | "observation" | "encounter";
  date: string;
  title: string;
  description?: string;
  status?: string;
  value?: string;
  unit?: string;
  raw?: Condition | Medication | Observation | Encounter;
}

function getEventIcon(type: TimelineEvent["type"]) {
  switch (type) {
    case "condition": return HeartPulse;
    case "medication": return Pill;
    case "observation": return FlaskConical;
    case "encounter": return Calendar;
  }
}

function getEventColor(type: TimelineEvent["type"]) {
  switch (type) {
    case "condition": return "text-red-500 bg-red-100 dark:bg-red-900/30";
    case "medication": return "text-blue-500 bg-blue-100 dark:bg-blue-900/30";
    case "observation": return "text-green-500 bg-green-100 dark:bg-green-900/30";
    case "encounter": return "text-purple-500 bg-purple-100 dark:bg-purple-900/30";
  }
}

function getStatusBadge(status?: string) {
  if (!status) return null;
  const isActive = status.toLowerCase() === "active" || status.toLowerCase() === "inpatient";
  return <Badge variant={isActive ? "success" : "secondary"} className="text-xs">{status}</Badge>;
}

export function PatientTimeline({ events }: { events: TimelineEvent[] }) {
  const sortedEvents = [...events].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  if (sortedEvents.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-neutral-500">No timeline events available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <ScrollArea className="max-h-[600px]">
          <div className="relative pl-6">
            <div className="absolute left-2 top-0 bottom-0 w-0.5 bg-neutral-200 dark:bg-neutral-700" />
            {sortedEvents.map((event, index) => {
              const Icon = getEventIcon(event.type);
              const isLast = index === sortedEvents.length - 1;

              return (
                <div key={event.id} className="relative pb-8 last:pb-4">
                  <div className="absolute left-[-6px] top-1 flex h-4 w-4 items-center justify-center">
                    <div className={cn("rounded-full border-2 border-white dark:border-neutral-900", getEventColor(event.type))}>
                      <Circle className="h-1.5 w-1.5 fill-current" />
                    </div>
                  </div>
                  {!isLast && (
                    <div className="absolute left-[-4px] top-6 bottom-0 w-0.5 bg-neutral-200 dark:bg-neutral-700" />
                  )}
                  <div className="ml-4 flex gap-4">
                    <div className={cn("p-2 rounded-lg shrink-0", getEventColor(event.type).replace("text-", "bg-").replace("bg-", "bg-"))}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0 pt-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-neutral-900 dark:text-white">{event.title}</p>
                        {getStatusBadge(event.status)}
                      </div>
                      <p className="text-sm text-neutral-500 dark:text-neutral-400">{event.description}</p>
                      {event.value && (
                        <p className="text-sm font-mono text-neutral-700 dark:text-neutral-300">
                          {event.value} {event.unit}
                        </p>
                      )}
                      <p className="mt-1 text-xs text-neutral-400 dark:text-neutral-500">{formatDateTime(event.date)}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}