import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import UploadZone from "./UploadZone";

describe("UploadZone", () => {
  it("associates the CSV file input with a label without nesting it in a button", () => {
    render(<UploadZone onFileAccepted={() => {}} />);

    const input = screen.getByLabelText("Choose a CSV file for Validex audit");
    expect(input).toHaveAttribute("type", "file");
    expect(input.closest("button")).toBeNull();
    expect(screen.getByRole("button", { name: /browse files/i })).toBeInTheDocument();
  });
});
