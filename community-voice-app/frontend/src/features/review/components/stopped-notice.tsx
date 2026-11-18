import { WarningAlert } from "@/components/shared/warning-alert";
import { Button } from "@/components/ui/button";

/** A step failed. Nothing was lost: the admin runs that step again. */
export const StoppedNotice = ({
  step,
  disabled,
  onRetry,
}: {
  step: string;
  disabled: boolean;
  onRetry: () => void;
}) => {
  return (
    <WarningAlert title="This report stopped">
      <p>It stopped while {step}. Nothing was lost: run that step again.</p>
      <Button className="mt-3" disabled={disabled} onClick={onRetry}>
        Retry
      </Button>
    </WarningAlert>
  );
};
