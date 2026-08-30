import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Input, Textarea, Select } from "@/components/ui/Input";

describe("Input", () => {
  it("renders input element", () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
  });

  it("renders with label", () => {
    render(<Input label="Username" />);
    expect(screen.getByText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
  });

  it("renders with error state", () => {
    render(<Input label="Email" error="Invalid email" />);
    expect(screen.getByText("Invalid email")).toBeInTheDocument();
    expect(screen.getByText("Invalid email")).toHaveClass("text-red-600");
  });

  it("renders with helper text", () => {
    render(<Input helperText="Must be at least 8 characters" />);
    expect(screen.getByText("Must be at least 8 characters")).toBeInTheDocument();
  });

  it("applies error styling", () => {
    render(<Input error="Error" />);
    expect(screen.getByRole("textbox")).toHaveClass("border-red-500");
  });

  it("handles ref forwarding", () => {
    const ref = { current: null };
    render(<Input ref={ref} />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it("passes additional props", () => {
    render(<Input data-testid="custom" maxLength={10} />);
    expect(screen.getByTestId("custom")).toHaveAttribute("maxlength", "10");
  });
});

describe("Textarea", () => {
  it("renders textarea element", () => {
    render(<Textarea placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
  });

  it("renders with label", () => {
    render(<Textarea label="Description" />);
    expect(screen.getByLabelText("Description")).toBeInTheDocument();
  });

  it("renders with error", () => {
    render(<Textarea error="Required" />);
    expect(screen.getByText("Required")).toBeInTheDocument();
  });

  it("handles ref forwarding", () => {
    const ref = { current: null };
    render(<Textarea ref={ref} />);
    expect(ref.current).toBeInstanceOf(HTMLTextAreaElement);
  });
});

describe("Select", () => {
  it("renders select element with options", () => {
    render(
      <Select options={[{ value: "a", label: "Option A" }, { value: "b", label: "Option B" }]} />
    );
    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(screen.getByText("Option A")).toBeInTheDocument();
    expect(screen.getByText("Option B")).toBeInTheDocument();
  });

  it("renders with label", () => {
    render(
      <Select label="Choose" options={[{ value: "a", label: "A" }]} />
    );
    expect(screen.getByLabelText("Choose")).toBeInTheDocument();
  });

  it("renders with placeholder", () => {
    render(
      <Select options={[{ value: "a", label: "A" }]} placeholder="Select..." />
    );
    expect(screen.getByText("Select...")).toBeInTheDocument();
  });
});
