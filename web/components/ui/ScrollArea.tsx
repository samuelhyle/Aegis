"use client";

import React, { useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, children, ...props }, ref) => {
    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const [showScrollbar, setShowScrollbar] = useState(false);

    useEffect(() => {
      const element = scrollAreaRef.current;
      if (!element) return;

      const handleScroll = () => setShowScrollbar(true);
      const handleLeave = () => setTimeout(() => setShowScrollbar(false), 1000);

      element.addEventListener("scroll", handleScroll);
      element.addEventListener("mouseenter", handleScroll);
      element.addEventListener("mouseleave", handleLeave);

      return () => {
        element.removeEventListener("scroll", handleScroll);
        element.removeEventListener("mouseenter", handleScroll);
        element.removeEventListener("mouseleave", handleLeave);
      };
    }, []);

    return (
      <div
        ref={scrollAreaRef}
        className={cn("relative overflow-auto scrollbar-hide", showScrollbar && "scrollbar-default", className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
ScrollArea.displayName = "ScrollArea";

interface ScrollBarProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: "horizontal" | "vertical";
}

export const ScrollBar = React.forwardRef<HTMLDivElement, ScrollBarProps>(
  ({ className, orientation = "vertical", ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex touch-none select-none transition-opacity",
        orientation === "vertical" ? "h-full w-1.5" : "h-1.5 w-full",
        className
      )}
      {...props}
    >
      <div
        className={cn(
          "relative rounded-full bg-neutral-300/50 dark:bg-neutral-600/50 transition-colors hover:bg-neutral-300 dark:hover:bg-neutral-600",
          orientation === "vertical" ? "h-16 w-full min-h-[40px]" : "h-full w-16 min-w-[40px]"
        )}
      />
    </div>
  )
);
ScrollBar.displayName = "ScrollBar";