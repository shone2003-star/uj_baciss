import { Suspense } from "react";
import type { Metadata } from "next";

import { LoadingState } from "@/components/shared/loading-state";
import { ReviewScreen } from "@/features/review/components/review-screen";

export const metadata: Metadata = { title: "Review queue" };

const ReviewPage = () => {
  // ReviewScreen reads the URL (?report=...), so it needs a Suspense boundary.
  return (
    <Suspense fallback={<LoadingState />}>
      <ReviewScreen />
    </Suspense>
  );
};

export default ReviewPage;
