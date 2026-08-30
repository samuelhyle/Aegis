import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  cn,
  formatDate,
  formatDateTime,
  formatRelativeTime,
  formatPercentage,
  formatNumber,
  truncate,
  getInitials,
  calculateAge,
  STATE_COLORS,
  STATE_LABELS,
  RISK_LEVEL_COLORS,
  RISK_LEVEL_LABELS,
  getStateColor,
  getStateLabel,
  getRiskColor,
  getRiskLabel,
  debounce,
  generateId,
} from "@/lib/utils/index";

describe("cn", () => {
  it("merges class names", () => {
    const result = cn("foo", "bar");
    expect(result).toContain("foo");
    expect(result).toContain("bar");
  });

  it("handles conditional classes", () => {
    const result = cn("foo", false && "bar", "baz");
    expect(result).toContain("foo");
    expect(result).not.toContain("bar");
    expect(result).toContain("baz");
  });

  it("deduplicates tailwind classes", () => {
    const result = cn("p-4", "p-8");
    expect(result).toBe("p-8");
  });

  it("handles undefined and empty inputs", () => {
    const result = cn(undefined, null, "", "foo");
    expect(result).toContain("foo");
  });
});

describe("formatDate", () => {
  it("formats a date string", () => {
    const result = formatDate("2024-01-15");
    expect(result).toMatch(/Jan 15, 2024/);
  });

  it("formats a Date object", () => {
    const result = formatDate(new Date("2024-06-20"));
    expect(result).toMatch(/Jun 20, 2024/);
  });

  it("accepts custom options", () => {
    const result = formatDate("2024-01-15", { weekday: "long" });
    expect(result).toMatch(/Monday/);
  });
});

describe("formatDateTime", () => {
  it("formats a date string with time", () => {
    const result = formatDateTime("2024-01-15T14:30:00");
    expect(result).toMatch(/Jan 15, 2024/);
    expect(result).toMatch(/\d{1,2}:\d{2}/);
  });
});

describe("formatRelativeTime", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns 'just now' for recent times", () => {
    vi.setSystemTime(new Date("2024-01-15T12:00:30"));
    const result = formatRelativeTime("2024-01-15T12:00:00");
    expect(result).toBe("just now");
  });

  it("returns minutes ago", () => {
    vi.setSystemTime(new Date("2024-01-15T12:05:00"));
    const result = formatRelativeTime("2024-01-15T12:00:00");
    expect(result).toBe("5m ago");
  });

  it("returns hours ago", () => {
    vi.setSystemTime(new Date("2024-01-15T14:00:00"));
    const result = formatRelativeTime("2024-01-15T12:00:00");
    expect(result).toBe("2h ago");
  });

  it("returns days ago", () => {
    vi.setSystemTime(new Date("2024-01-18T12:00:00"));
    const result = formatRelativeTime("2024-01-15T12:00:00");
    expect(result).toBe("3d ago");
  });

  it("returns formatted date for older times", () => {
    vi.setSystemTime(new Date("2024-02-15T12:00:00"));
    const result = formatRelativeTime("2024-01-15T12:00:00");
    expect(result).toMatch(/Jan 15, 2024/);
  });
});

describe("formatPercentage", () => {
  it("formats a percentage", () => {
    expect(formatPercentage(0.5)).toBe("50%");
  });

  it("formats with decimals", () => {
    expect(formatPercentage(0.123, 1)).toBe("12.3%");
  });

  it("handles zero", () => {
    expect(formatPercentage(0)).toBe("0%");
  });

  it("handles 100%", () => {
    expect(formatPercentage(1)).toBe("100%");
  });
});

describe("formatNumber", () => {
  it("formats a number with commas", () => {
    expect(formatNumber(1234567)).toBe("1,234,567");
  });

  it("handles zero", () => {
    expect(formatNumber(0)).toBe("0");
  });

  it("handles small numbers", () => {
    expect(formatNumber(42)).toBe("42");
  });
});

describe("truncate", () => {
  it("returns the original string if shorter than limit", () => {
    expect(truncate("hello", 10)).toBe("hello");
  });

  it("truncates to the specified length", () => {
    expect(truncate("hello world", 5)).toBe("hello...");
  });

  it("handles exact length", () => {
    expect(truncate("hello", 5)).toBe("hello");
  });

  it("handles empty string", () => {
    expect(truncate("", 5)).toBe("");
  });
});

describe("getInitials", () => {
  it("returns first letters of names", () => {
    expect(getInitials("John", "Doe")).toBe("JD");
  });

  it("handles single character names", () => {
    expect(getInitials("A", "B")).toBe("AB");
  });

  it("handles empty strings", () => {
    expect(getInitials("", "")).toBe("");
  });

  it("handles undefined gracefully", () => {
    expect(getInitials(undefined as unknown as string, "Doe")).toBe("D");
  });
});

describe("calculateAge", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2024-06-15"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("calculates correct age", () => {
    expect(calculateAge("1990-01-01")).toBe(34);
  });

  it("accounts for birthday not yet occurred this year", () => {
    expect(calculateAge("1990-12-25")).toBe(33);
  });

  it("handles birthday today", () => {
    expect(calculateAge("1990-06-15")).toBe(34);
  });
});

describe("STATE_COLORS", () => {
  it("has expected keys", () => {
    expect(STATE_COLORS).toHaveProperty("stable");
    expect(STATE_COLORS).toHaveProperty("acute");
    expect(STATE_COLORS).toHaveProperty("recovery");
    expect(STATE_COLORS).toHaveProperty("chronic");
  });
});

describe("STATE_LABELS", () => {
  it("has expected keys with capitalized labels", () => {
    expect(STATE_LABELS.stable).toBe("Stable");
    expect(STATE_LABELS.acute).toBe("Acute");
  });
});

describe("RISK_LEVEL_COLORS", () => {
  it("has all risk levels", () => {
    expect(RISK_LEVEL_COLORS).toHaveProperty("low");
    expect(RISK_LEVEL_COLORS).toHaveProperty("moderate");
    expect(RISK_LEVEL_COLORS).toHaveProperty("high");
    expect(RISK_LEVEL_COLORS).toHaveProperty("very_high");
    expect(RISK_LEVEL_COLORS).toHaveProperty("critical");
  });
});

describe("RISK_LEVEL_LABELS", () => {
  it("has all risk levels with labels", () => {
    expect(RISK_LEVEL_LABELS.low).toBe("Low");
    expect(RISK_LEVEL_LABELS.very_high).toBe("Very High");
  });
});

describe("getStateColor", () => {
  it("returns correct color for known state", () => {
    expect(getStateColor("stable")).toBe("bg-green-500");
  });

  it("is case-insensitive", () => {
    expect(getStateColor("STABLE")).toBe("bg-green-500");
  });

  it("returns default for unknown state", () => {
    expect(getStateColor("unknown")).toBe("bg-gray-500");
  });
});

describe("getStateLabel", () => {
  it("returns correct label", () => {
    expect(getStateLabel("stable")).toBe("Stable");
  });

  it("is case-insensitive", () => {
    expect(getStateLabel("ACUTE")).toBe("Acute");
  });

  it("returns raw string for unknown state", () => {
    expect(getStateLabel("unknown")).toBe("unknown");
  });
});

describe("getRiskColor", () => {
  it("returns correct color for known level", () => {
    expect(getRiskColor("low")).toBe("bg-green-100 text-green-800");
  });

  it("is case-insensitive", () => {
    expect(getRiskColor("HIGH")).toBe("bg-orange-100 text-orange-800");
  });

  it("returns default for unknown level", () => {
    expect(getRiskColor("unknown")).toBe("bg-gray-100 text-gray-800");
  });
});

describe("getRiskLabel", () => {
  it("returns correct label", () => {
    expect(getRiskLabel("low")).toBe("Low");
  });

  it("is case-insensitive", () => {
    expect(getRiskLabel("VERY_HIGH")).toBe("Very High");
  });

  it("returns raw string for unknown level", () => {
    expect(getRiskLabel("unknown")).toBe("unknown");
  });
});

describe("debounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("delays function execution", () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 500);
    debounced();
    expect(fn).not.toHaveBeenCalled();
    vi.advanceTimersByTime(500);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("resets timer on subsequent calls", () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 500);
    debounced();
    vi.advanceTimersByTime(300);
    debounced();
    vi.advanceTimersByTime(300);
    expect(fn).not.toHaveBeenCalled();
    vi.advanceTimersByTime(200);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("passes arguments to the function", () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);
    debounced("arg1", "arg2");
    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledWith("arg1", "arg2");
  });
});

describe("generateId", () => {
  it("generates a string", () => {
    const id = generateId();
    expect(typeof id).toBe("string");
  });

  it("generates unique ids", () => {
    const ids = new Set(Array.from({ length: 100 }, () => generateId()));
    expect(ids.size).toBe(100);
  });
});
