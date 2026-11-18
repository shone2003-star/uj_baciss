import { useState, type FormEvent } from "react";
import { toast } from "sonner";

import { PrivacyConsent } from "@/components/shared/privacy-consent";
import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import { useSendMessage } from "@/features/chat/hooks";
import { MAX_MESSAGE_CHARS } from "@/features/chat/schemas";
import { ApiError } from "@/lib/api-client";

/** The citizen's message box. Their text is made private on the server first. */
export const CitizenComposer = ({ reportId }: { reportId: string }) => {
  const [text, setText] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [filterDown, setFilterDown] = useState(false);
  const send = useSendMessage(reportId);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    send.mutate(
      { body: text.trim(), allow_unfiltered: agreed },
      {
        onSuccess: () => {
          setText("");
          setAgreed(false);
          setFilterDown(false);
        },
        onError: (error) => {
          // On this endpoint a 503 can only mean the local privacy filter is down.
          if (error instanceof ApiError && error.status === 503) setFilterDown(true);
          else toast.error(error.message);
        },
      },
    );
  };

  const blocked = send.isPending || !text.trim() || (filterDown && !agreed);

  return (
    <form onSubmit={submit} className="space-y-3">
      <Field>
        <FieldLabel htmlFor="message">Your message</FieldLabel>
        <Textarea
          id="message"
          rows={4}
          maxLength={MAX_MESSAGE_CHARS}
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <FieldDescription>
          {text.length} / {MAX_MESSAGE_CHARS}. Personal details are removed before an AI
          reads your message.
        </FieldDescription>
      </Field>
      {filterDown && <PrivacyConsent agreed={agreed} onChange={setAgreed} />}
      <Button type="submit" disabled={blocked}>
        {send.isPending ? "Sending…" : "Send"}
      </Button>
    </form>
  );
};
