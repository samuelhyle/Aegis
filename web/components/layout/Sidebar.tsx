"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  Search,
  Activity,
  GitGraph,
  TrendingUp,
  FlaskConical,
  Pill,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/Tooltip";

const navigation = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Patients", href: "/patients", icon: Users },
  { name: "Investigations", href: "/investigations", icon: Search },
  { name: "Vector Search", href: "/search", icon: Search },
  { name: "Analytics", href: "/analytics", icon: TrendingUp, children: [
    { name: "Risk Dashboard", href: "/analytics/risk", icon: Activity },
    { name: "Temporal Analysis", href: "/analytics/temporal", icon: GitGraph },
    { name: "Graph RAG Explorer", href: "/analytics/graph-rag", icon: FlaskConical },
    { name: "Evaluation", href: "/analytics/evaluation", icon: TrendingUp },
    { name: "Benchmark", href: "/analytics/benchmark", icon: TrendingUp },
  ]},
  { name: "Clinical Trials", href: "/clinical-trials", icon: FlaskConical },
  { name: "Drug Interactions", href: "/drug-interactions", icon: Pill },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar({
  onCollapse,
  mobileOpen,
  onMobileClose,
}: {
  onCollapse?: (collapsed: boolean) => void;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  const handleCollapse = (newCollapsed: boolean) => {
    setCollapsed(newCollapsed);
    onCollapse?.(newCollapsed);
  };

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen border-r border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-950 transition-all duration-300",
        collapsed ? "w-16" : "w-64",
        "max-lg:hidden",
        mobileOpen && "max-lg:!flex max-lg:w-64"
      )}
    >
      <div className="flex h-full flex-col">
        <div className={cn(
          "flex h-16 items-center border-b border-neutral-200 dark:border-neutral-800",
          collapsed ? "justify-center" : "gap-2 px-6"
        )}>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
            <Activity className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <span className="text-xl font-bold text-neutral-900 dark:text-white">AEGIS</span>
          )}
        </div>

        <nav className="flex-1 overflow-y-auto p-4 space-y-1" aria-label="Main navigation">
          {navigation.map((item) => {
            const isActive = pathname === item.href || (item.children && pathname.startsWith(item.href));
            const isParentActive = item.children && pathname.startsWith(item.href);

            if (item.children) {
              return (
                <div key={item.name} className="space-y-1">
                  {collapsed ? (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          className={cn(
                            "flex w-full items-center justify-center rounded-lg p-2 transition-colors",
                            isParentActive
                              ? "text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/20"
                              : "text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-white dark:hover:bg-neutral-800"
                          )}
                          aria-expanded={isParentActive}
                        >
                          <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent side="right">{item.name}</TooltipContent>
                    </Tooltip>
                  ) : (
                    <>
                      <button
                        className={cn(
                          "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                          isParentActive
                            ? "text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/20"
                            : "text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-white dark:hover:bg-neutral-800"
                        )}
                        aria-expanded={isParentActive}
                      >
                        <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                        <span className="flex-1">{item.name}</span>
                        <svg
                          className={cn("h-4 w-4 shrink-0 transition-transform", isParentActive && "rotate-180")}
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="m6 9 6 6 6-6" />
                        </svg>
                      </button>
                      {isParentActive && (
                        <div className="pl-10 space-y-0.5 animate-fade-in">
                          {item.children.map((child) => (
                            <Link
                              key={child.name}
                              href={child.href}
                              onClick={onMobileClose}
                              className={cn(
                                "flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors",
                                pathname === child.href
                                  ? "text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/20"
                                  : "text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-white dark:hover:bg-neutral-800"
                              )}
                            >
                              <child.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                              {child.name}
                            </Link>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              );
            }

            return collapsed ? (
              <Tooltip key={item.name}>
                <TooltipTrigger asChild>
                  <Link
                    href={item.href}
                    className={cn(
                      "flex w-full items-center justify-center rounded-lg p-2 transition-colors",
                      isActive
                        ? "text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/20"
                        : "text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-white dark:hover:bg-neutral-800"
                    )}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right">{item.name}</TooltipContent>
              </Tooltip>
            ) : (
              <Link
                key={item.name}
                href={item.href}
                onClick={onMobileClose}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/20"
                    : "text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-white dark:hover:bg-neutral-800"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-neutral-200 p-4 dark:border-neutral-800">
          <button
            onClick={() => handleCollapse(!collapsed)}
            className="w-full flex items-center justify-center gap-2 rounded-lg p-2 text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-white dark:hover:bg-neutral-800 transition-colors"
          >
            {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
          </button>
        </div>
      </div>
    </aside>
  );
}
