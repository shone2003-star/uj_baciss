import { WarningAlert } from "@/components/shared/warning-alert";

/** Shown when the local privacy filter is down. The citizen must agree to go on. */
export const PrivacyConsent = ({
  agreed,
  onChange,
}: {
  agreed: boolean;
  onChange: (agreed: boolean) => void;
}) => {
  return (
    <WarningAlert title="Privacy filter not available">
      <p>
        The tool that removes personal details on this computer could not be reached.
        Only phone numbers, ID numbers and emails will be removed. Names and addresses
        may be sent to the AI services.
      </p>
      <label className="mt-3 flex items-start gap-2 font-medium">
        <input
          type="checkbox"
          className="mt-1 size-4"
          checked={agreed}
          onChange={(event) => onChange(event.target.checked)}
        />
        I understand and agree to continue.
      </label>
    </WarningAlert>
  );
};
