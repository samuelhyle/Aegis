"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useTheme } from "@/components/providers/ThemeProvider";
import { useSystemHealth, useSystemStats } from "@/lib/hooks/useQueries";
import { apiClient } from "@/lib/api/client";
import { Sun, Moon, Monitor, Server, Activity, Shield, Key } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { data: healthData } = useSystemHealth();
  const { data: statsData } = useSystemStats();
  const [apiKey, setApiKey] = useState(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem("aegis-api-key") || "";
  });
  const [apiKeySaved, setApiKeySaved] = useState(false);

  useEffect(() => {
    if (apiKey) {
      apiClient.setApiKey(apiKey);
    }
  }, [apiKey]);

  const handleSaveApiKey = () => {
    if (apiKey) {
      localStorage.setItem("aegis-api-key", apiKey);
      apiClient.setApiKey(apiKey);
    } else {
      localStorage.removeItem("aegis-api-key");
      apiClient.setApiKey("");
    }
    setApiKeySaved(true);
    setTimeout(() => setApiKeySaved(false), 2000);
  };

  const themeOptions = [
    { value: "light" as const, label: "Light", icon: Sun },
    { value: "dark" as const, label: "Dark", icon: Moon },
    { value: "system" as const, label: "System", icon: Monitor },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">Settings</h1>
        <p className="text-neutral-500 dark:text-neutral-400">Configure your application preferences</p>
      </div>

      {/* Theme Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sun className="h-5 w-5" />
            Appearance
          </CardTitle>
          <CardDescription>Customize the look and feel of the application</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            {themeOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setTheme(option.value)}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 rounded-lg border-2 transition-colors",
                  theme === option.value
                    ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                    : "border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600"
                )}
              >
                <option.icon className="h-5 w-5" />
                <span className="font-medium">{option.label}</span>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            API Configuration
          </CardTitle>
          <CardDescription>Configure API access for enhanced features</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              API Key (Optional)
            </label>
            <div className="flex gap-3">
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="flex-1 px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg"
              />
              <Button onClick={handleSaveApiKey}>
                {apiKeySaved ? "Saved!" : "Save"}
              </Button>
            </div>
            <p className="mt-2 text-sm text-neutral-500">
              API key is stored locally in your browser. Required for administrative actions.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            System Status
          </CardTitle>
          <CardDescription>Current system health and statistics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="h-4 w-4" />
                <span className="font-medium">Backend Status</span>
              </div>
              <div className="flex items-center gap-2">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  healthData?.status === "healthy" ? "bg-green-500" : "bg-red-500"
                )} />
                <span className="text-sm text-neutral-600 dark:text-neutral-400">
                  {healthData?.status || "Unknown"} - {healthData?.service || "AEGIS"}
                </span>
              </div>
            </div>
            <div className="p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="h-4 w-4" />
                <span className="font-medium">Version</span>
              </div>
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                {healthData?.version || "Unknown"}
              </span>
            </div>
          </div>

          {statsData && (
            <div className="mt-4 grid gap-4 sm:grid-cols-4">
              <div className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900 text-center">
                <p className="text-2xl font-bold text-neutral-900 dark:text-white">{statsData.total_patients || 0}</p>
                <p className="text-xs text-neutral-500">Patients</p>
              </div>
              <div className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900 text-center">
                <p className="text-2xl font-bold text-neutral-900 dark:text-white">{statsData.active_investigations || 0}</p>
                <p className="text-xs text-neutral-500">Active Investigations</p>
              </div>
              <div className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900 text-center">
                <p className="text-2xl font-bold text-neutral-900 dark:text-white">{statsData.high_risk_alerts || 0}</p>
                <p className="text-xs text-neutral-500">High Risk Alerts</p>
              </div>
              <div className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900 text-center">
                <p className="text-2xl font-bold text-neutral-900 dark:text-white">{statsData.pending_reviews || 0}</p>
                <p className="text-xs text-neutral-500">Pending Reviews</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
