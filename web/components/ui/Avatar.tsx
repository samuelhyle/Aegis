"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { getInitials } from "@/lib/utils";

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: "sm" | "md" | "lg" | "xl";
}

const sizes = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-12 w-12 text-base",
  xl: "h-16 w-16 text-lg",
};

export const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, src, alt, fallback, size = "md", ...props }, ref) => {
    const [imageError, setImageError] = React.useState(false);

    if (src && !imageError) {
      return (
        <div
          ref={ref}
          className={cn("relative inline-flex shrink-0 overflow-hidden rounded-full", sizes[size], className)}
          {...props}
        >
          <img
            src={src}
            alt={alt || fallback || "Avatar"}
            className="aspect-square h-full w-full object-cover"
            onError={() => setImageError(true)}
          />
        </div>
      );
    }

    return (
      <div
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-full bg-neutral-100 font-medium text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300",
          sizes[size],
          className
        )}
        {...props}
      >
        {fallback || "?"}
      </div>
    );
  }
);
Avatar.displayName = "Avatar";

export const AvatarWithFallback = ({
  src,
  alt,
  firstName,
  lastName,
  size = "md",
  className,
}: AvatarProps & { firstName?: string; lastName?: string }) => (
  <Avatar
    src={src}
    alt={alt}
    fallback={firstName || lastName ? getInitials(firstName || "", lastName || "") : undefined}
    size={size}
    className={className}
  />
);