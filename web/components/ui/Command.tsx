"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Search } from "lucide-react";
import { Dialog, DialogContent } from "./Dialog";

interface CommandContextType {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  search: string;
  setSearch: (search: string) => void;
  selectedValue: string;
  setSelectedValue: (value: string) => void;
}

const CommandContext = createContext<CommandContextType | undefined>(undefined);

function useCommand() {
  const context = useContext(CommandContext);
  if (!context) {
    throw new Error("Command components must be used within a Command provider");
  }
  return context;
}

interface CommandProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

export function Command({ open: controlledOpen, onOpenChange, children }: CommandProps) {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedValue, setSelectedValue] = useState("");
  const open = controlledOpen ?? uncontrolledOpen;
  const setOpen = onOpenChange ?? setUncontrolledOpen;

  return (
    <CommandContext.Provider value={{ open, onOpenChange: setOpen, search, setSearch, selectedValue, setSelectedValue }}>
      <Dialog open={open} onOpenChange={setOpen}>
        {children}
      </Dialog>
    </CommandContext.Provider>
  );
}

interface CommandInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  icon?: React.ReactNode;
}

export const CommandInput = React.forwardRef<HTMLInputElement, CommandInputProps>(
  ({ className, icon, ...props }, ref) => {
    const { search, setSearch } = useCommand();

    return (
      <div className="flex items-center border-b border-neutral-200 px-3 dark:border-neutral-800">
        {icon || <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />}
        <input
          ref={ref}
          type="text"
          className={cn(
            "flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-neutral-500 disabled:cursor-not-allowed disabled:opacity-50 dark:placeholder:text-neutral-400",
            className
          )}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          {...props}
        />
      </div>
    );
  }
);
CommandInput.displayName = "CommandInput";

type CommandListProps = React.HTMLAttributes<HTMLDivElement>

export const CommandList = React.forwardRef<HTMLDivElement, CommandListProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("max-h-[300px] overflow-y-auto overflow-x-hidden p-2", className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
CommandList.displayName = "CommandList";

type CommandEmptyProps = React.HTMLAttributes<HTMLDivElement>

export const CommandEmpty = React.forwardRef<HTMLDivElement, CommandEmptyProps>(
  ({ className, ...props }, ref) => {
    const { search } = useCommand();

    if (search) {
      return null;
    }

    return (
      <div
        ref={ref}
        className={cn("py-6 text-center text-sm text-neutral-500 dark:text-neutral-400", className)}
        {...props}
      />
    );
  }
);
CommandEmpty.displayName = "CommandEmpty";

interface CommandGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  heading?: string;
}

export const CommandGroup = React.forwardRef<HTMLDivElement, CommandGroupProps>(
  ({ className, heading, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("mb-2", className)}
        {...props}
      >
        {heading && (
          <div className="px-2 py-1.5 text-xs font-medium text-neutral-500 dark:text-neutral-400">
            {heading}
          </div>
        )}
        <div className="space-y-0.5">{children}</div>
      </div>
    );
  }
);
CommandGroup.displayName = "CommandGroup";

interface CommandItemProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "onSelect"> {
  value: string;
  onSelect?: (value: string) => void;
}

export const CommandItem = React.forwardRef<HTMLDivElement, CommandItemProps>(
  ({ className, value, onSelect, children, ...props }, ref) => {
    const { search, selectedValue, setSelectedValue } = useCommand();
    const isSelected = selectedValue === value;

    const matchesSearch = !search || 
      value.toLowerCase().includes(search.toLowerCase()) ||
      (typeof children === "string" && children.toLowerCase().includes(search.toLowerCase()));

    if (!matchesSearch) {
      return null;
    }

    return (
      <div
        ref={ref}
        className={cn(
          "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-neutral-100 hover:text-neutral-900 data-[disabled]:pointer-events-none data-[disabled]:opacity-50 dark:hover:bg-neutral-800 dark:hover:text-neutral-50",
          isSelected && "bg-neutral-100 dark:bg-neutral-800",
          className
        )}
        onClick={() => {
          setSelectedValue(value);
          onSelect?.(value);
        }}
        {...props}
      >
        {children}
      </div>
    );
  }
);
CommandItem.displayName = "CommandItem";

type CommandSeparatorProps = React.HTMLAttributes<HTMLDivElement>

export const CommandSeparator = React.forwardRef<HTMLDivElement, CommandSeparatorProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("-mx-1 my-1 h-px bg-neutral-200 dark:bg-neutral-800", className)}
      {...props}
    />
  )
);
CommandSeparator.displayName = "CommandSeparator";

type CommandShortcutProps = React.HTMLAttributes<HTMLSpanElement>

export const CommandShortcut = React.forwardRef<HTMLSpanElement, CommandShortcutProps>(
  ({ className, ...props }, ref) => (
    <span
      ref={ref}
      className={cn("ml-auto text-xs tracking-widest text-neutral-500 dark:text-neutral-400", className)}
      {...props}
    />
  )
);
CommandShortcut.displayName = "CommandShortcut";

export function CommandDialog({ children, ...props }: CommandProps) {
  return (
    <Command {...props}>
      <DialogContent className="overflow-hidden p-0 shadow-lg">
        {children}
      </DialogContent>
    </Command>
  );
}

export function useCommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  return { open, setOpen };
}
