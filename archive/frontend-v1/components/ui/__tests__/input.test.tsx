import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Input } from "../input";

describe("Input", () => {
  it("renders correctly", () => {
    render(<Input placeholder="Enter text" />);
    const input = screen.getByPlaceholderText(/enter text/i);
    expect(input).toBeInTheDocument();
  });

  it("handles user input", async () => {
    const user = userEvent.setup();
    render(<Input placeholder="Type here" />);

    const input = screen.getByPlaceholderText(/type here/i);
    await user.type(input, "Hello World");

    expect(input).toHaveValue("Hello World");
  });

  it("handles onChange events", async () => {
    const handleChange = jest.fn();
    const user = userEvent.setup();

    render(<Input onChange={handleChange} placeholder="Test" />);

    const input = screen.getByPlaceholderText(/test/i);
    await user.type(input, "A");

    expect(handleChange).toHaveBeenCalled();
  });

  it("renders with different types", () => {
    const { rerender } = render(<Input type="email" />);
    expect(screen.getByRole("textbox")).toHaveAttribute("type", "email");

    rerender(<Input type="password" />);
    const passwordInput = document.querySelector('input[type="password"]');
    expect(passwordInput).toBeInTheDocument();
  });

  it("is disabled when disabled prop is true", async () => {
    const user = userEvent.setup();
    render(<Input disabled placeholder="Disabled" />);

    const input = screen.getByPlaceholderText(/disabled/i);
    expect(input).toBeDisabled();
    expect(input).toHaveClass("disabled:opacity-50");

    await user.type(input, "Should not type");
    expect(input).toHaveValue("");
  });

  it("applies custom className", () => {
    render(<Input className="custom-input" placeholder="Custom" />);
    expect(screen.getByPlaceholderText(/custom/i)).toHaveClass("custom-input");
  });

  it("forwards ref correctly", () => {
    const ref = jest.fn();
    render(<Input ref={ref} />);
    expect(ref).toHaveBeenCalled();
  });

  it("supports required attribute", () => {
    render(<Input required placeholder="Required field" />);
    expect(screen.getByPlaceholderText(/required field/i)).toBeRequired();
  });

  it("supports aria attributes for accessibility", () => {
    render(
      <Input
        aria-label="Email address"
        aria-describedby="email-help"
        placeholder="Email"
      />
    );
    const input = screen.getByLabelText(/email address/i);
    expect(input).toHaveAttribute("aria-describedby", "email-help");
  });
});
