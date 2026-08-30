"use client";

import { Bell, Search, User, Menu, Settings, LogOut, Sun, Moon, Monitor, Command } from "lucide-react";
import { AvatarWithFallback } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { useState, useRef, useEffect } from "react";
import { useTheme } from "@/components/providers/ThemeProvider";
import { useAuth } from "@/lib/auth/context";
import { CommandDialog, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem, CommandShortcut } from "@/components/ui/Command";
import { useRouter } from "next/navigation";

function ThemeIcon({ theme }: { theme: "light" | "dark" | "system" }) {
  switch (theme) {
    case "light":
      return <Sun className="h-5 w-5" />;
    case "dark":
      return <Moon className="h-5 w-5" />;
    case "system":
      return <Monitor className="h-5 w-5" />;
  }
}

export function Header({ onToggleMobile }: { onToggleMobile?: () => void }) {
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const notificationsRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notificationsRef.current && !notificationsRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCommandOpen(true);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  const cycleTheme = () => {
    const themes: Array<"light" | "dark" | "system"> = ["light", "dark", "system"];
    const currentIndex = themes.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setTheme(themes[nextIndex]);
  };

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-neutral-200 bg-white/80 px-4 backdrop-blur-sm dark:border-neutral-800 dark:bg-neutral-950/80">
        <button
          onClick={onToggleMobile}
          className="lg:hidden p-2 rounded-lg text-neutral-500 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800"
          aria-label="Toggle navigation menu"
        >
          <Menu className="h-6 w-6" />
        </button>

        <button
          onClick={() => setCommandOpen(true)}
          className="flex items-center gap-2 rounded-lg border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm text-neutral-500 hover:bg-neutral-100 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800"
        >
          <Search className="h-4 w-4" />
          <span className="hidden sm:inline">Search patients, investigations...</span>
          <kbd className="pointer-events-none hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border border-neutral-200 bg-white px-1.5 font-mono text-[10px] font-medium text-neutral-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400">
            <Command className="h-3 w-3" />K
          </kbd>
        </button>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={cycleTheme}
            aria-label={`Switch to ${theme === "light" ? "dark" : theme === "dark" ? "system" : "light"} mode`}
          >
            <ThemeIcon theme={theme} />
          </Button>

          <Button variant="ghost" size="icon" onClick={() => setNotificationsOpen(!notificationsOpen)} aria-label="Notifications" aria-expanded={notificationsOpen}>
            <Bell className="h-5 w-5 text-neutral-500" />
          </Button>

          <div className="relative" ref={notificationsRef}>
            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 rounded-xl border border-neutral-200 bg-white py-2 shadow-lg dark:border-neutral-800 dark:bg-neutral-900 animate-fade-in">
                <div className="px-4 py-2 border-b border-neutral-200 dark:border-neutral-800">
                  <h3 className="font-semibold text-neutral-900 dark:text-white">Notifications</h3>
                </div>
                <div className="max-h-60 overflow-y-auto">
                  <div className="px-4 py-8 text-center text-neutral-500 dark:text-neutral-400">
                    <p className="text-sm">No new notifications</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 rounded-lg p-1 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              aria-label="User menu"
              aria-expanded={userMenuOpen}
            >
              <AvatarWithFallback firstName={user?.firstName || "User"} lastName={user?.lastName || ""} size="sm" />
              <span className="hidden sm:block text-sm font-medium text-neutral-700 dark:text-neutral-300">{user?.displayName || "User"}</span>
            </button>
            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 rounded-xl border border-neutral-200 bg-white py-2 shadow-lg dark:border-neutral-800 dark:bg-neutral-900 animate-fade-in">
                <div className="px-4 py-3 border-b border-neutral-200 dark:border-neutral-800">
                  <p className="font-medium text-neutral-900 dark:text-white">{user?.displayName || "User"}</p>
                  <p className="text-sm text-neutral-500 dark:text-neutral-400">{user?.role || "User"}</p>
                </div>
                <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50 dark:text-neutral-300 dark:hover:bg-neutral-800">
                  <User className="h-4 w-4" />
                  Profile
                </button>
                <button
                  onClick={() => { router.push("/settings"); setUserMenuOpen(false); }}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50 dark:text-neutral-300 dark:hover:bg-neutral-800"
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </button>
                <hr className="my-2 border-neutral-200 dark:border-neutral-800" />
                <button
                  onClick={() => { logout(); router.push("/login"); setUserMenuOpen(false); }}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <CommandDialog open={commandOpen} onOpenChange={setCommandOpen}>
        <CommandInput placeholder="Type a command or search..." />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          <CommandGroup heading="Navigation">
            <CommandItem value="dashboard" onSelect={() => { router.push("/dashboard"); setCommandOpen(false); }}>
              <span>Dashboard</span>
              <CommandShortcut>/d</CommandShortcut>
            </CommandItem>
            <CommandItem value="patients" onSelect={() => { router.push("/patients"); setCommandOpen(false); }}>
              <span>Patients</span>
              <CommandShortcut>/p</CommandShortcut>
            </CommandItem>
            <CommandItem value="investigations" onSelect={() => { router.push("/investigations"); setCommandOpen(false); }}>
              <span>Investigations</span>
              <CommandShortcut>/i</CommandShortcut>
            </CommandItem>
            <CommandItem value="risk-analytics" onSelect={() => { router.push("/analytics/risk"); setCommandOpen(false); }}>
              <span>Risk Analytics</span>
              <CommandShortcut>/ar</CommandShortcut>
            </CommandItem>
            <CommandItem value="temporal-analysis" onSelect={() => { router.push("/analytics/temporal"); setCommandOpen(false); }}>
              <span>Temporal Analysis</span>
              <CommandShortcut>/at</CommandShortcut>
            </CommandItem>
          </CommandGroup>
          <CommandGroup heading="Actions">
            <CommandItem value="new-investigation" onSelect={() => { router.push("/patients"); setCommandOpen(false); }}>
              <span>New Investigation</span>
              <CommandShortcut>n</CommandShortcut>
            </CommandItem>
            <CommandItem value="toggle-theme" onSelect={() => { setTheme(theme === "dark" ? "light" : "dark"); setCommandOpen(false); }}>
              <span>Toggle Theme</span>
              <CommandShortcut>t</CommandShortcut>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  );
}
