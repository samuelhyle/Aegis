"use client";

import React, { createContext, useContext, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface TabsContextType {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  variant: "default" | "pills" | "underline";
}

const TabsContext = createContext<TabsContextType | null>(null);

function useTabsContext() {
  const context = useContext(TabsContext);
  if (!context) throw new Error("Tabs components must be used within Tabs.Root");
  return context;
}

interface TabsRootProps {
  defaultValue: string;
  value?: string;
  onChange?: (value: string) => void;
  variant?: "default" | "pills" | "underline";
  children: ReactNode;
  className?: string;
}

export function TabsRoot({ defaultValue, value, onChange, variant = "default", children, className }: TabsRootProps) {
  const [activeTab, setActiveTab] = useState(value || defaultValue);

  const handleChange = (tab: string) => {
    if (value === undefined) setActiveTab(tab);
    onChange?.(tab);
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleChange, variant }}>
      <div className={cn("flex flex-col", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

interface TabsListProps {
  children: ReactNode;
  className?: string;
}

export function TabsList({ children, className }: TabsListProps) {
  const { variant } = useTabsContext();

  const baseStyles = "flex items-center gap-1";
  const variants = {
    default: "bg-neutral-100 p-1 rounded-lg dark:bg-neutral-800",
    pills: "",
    underline: "border-b border-neutral-200 dark:border-neutral-700",
  };

  return (
    <div role="tablist" className={cn(baseStyles, variants[variant], className)}>
      {children}
    </div>
  );
}

interface TabsTriggerProps {
  value: string;
  children: ReactNode;
  disabled?: boolean;
  className?: string;
}

export function TabsTrigger({ value, children, disabled, className }: TabsTriggerProps) {
  const { activeTab, setActiveTab, variant } = useTabsContext();
  const isActive = activeTab === value;

  const baseStyles = "flex items-center justify-center px-4 py-2 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  const variants = {
    default: cn(
      "rounded-md",
      isActive && "bg-white text-primary-600 shadow-sm dark:bg-neutral-800 dark:text-primary-400",
      !isActive && "text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100"
    ),
    pills: cn(
      "rounded-md",
      isActive && "bg-primary-600 text-white shadow-sm",
      !isActive && "text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800"
    ),
    underline: cn(
      "border-b-2 -mb-px",
      isActive && "border-primary-600 text-primary-600 dark:text-primary-400",
      !isActive && "border-transparent text-neutral-500 hover:text-neutral-900 hover:border-neutral-300 dark:text-neutral-400 dark:hover:border-neutral-600"
    ),
  };

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-controls={`panel-${value}`}
      id={`tab-${value}`}
      onClick={() => !disabled && setActiveTab(value)}
      disabled={disabled}
      className={cn(baseStyles, variants[variant], className)}
    >
      {children}
    </button>
  );
}

interface TabsContentProps {
  value: string;
  children: ReactNode;
  className?: string;
}

export function TabsContent({ value, children, className }: TabsContentProps) {
  const { activeTab } = useTabsContext();
  const isActive = activeTab === value;

  if (!isActive) return null;

  return (
    <div
      role="tabpanel"
      id={`panel-${value}`}
      aria-labelledby={`tab-${value}`}
      className={cn("mt-4 animate-fade-in", className)}
    >
      {children}
    </div>
  );
}

export const Tabs = Object.assign(TabsRoot, {
  List: TabsList,
  Trigger: TabsTrigger,
  Content: TabsContent,
});