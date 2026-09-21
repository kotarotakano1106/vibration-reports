import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AnalysisProgress } from "@/features/analysis/components/AnalysisProgress";

describe("AnalysisProgress", () => {
  it("renders nothing when inactive", () => {
    const { container } = render(<AnalysisProgress active={false} />);

    expect(container).toBeEmptyDOMElement();
    expect(
      screen.queryByText("CSVを確認しています..."),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("shows the progress message and indicator when active", () => {
    render(<AnalysisProgress active />);

    expect(screen.getByText("CSVを確認しています...")).toBeVisible();
    expect(screen.getByRole("progressbar")).toBeVisible();
  });
});
