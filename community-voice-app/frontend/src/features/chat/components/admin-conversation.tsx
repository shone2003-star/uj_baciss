import { useState } from "react";
import { toast } from "sonner";

import { QueryBoundary } from "@/components/shared/query-boundary";
import { WarningAlert } from "@/components/shared/warning-alert";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldLabel } from "@/components/ui/field";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { MessageList } from "@/features/chat/components/message-list";
import { ReportDetailsDialog } from "@/features/review/components/report-details-dialog";
import {
  useCloseThread,
  useSendMessage,
  useSuggestReply,
  useThread,
} from "@/features/chat/hooks";
import { MAX_MESSAGE_CHARS, type Suggestion } from "@/features/chat/schemas";

/** One conversation, as the admin sees it: read, get a suggestion, reply, close. */
export const AdminConversation = ({ reportId }: { reportId: string }) => {
  const thread = useThread(reportId);
  const send = useSendMessage(reportId);
  const suggest = useSuggestReply(reportId);
  const close = useCloseThread(reportId);
  const [reply, setReply] = useState("");
  const [note, setNote] = useState<Suggestion | null>(null);
  const [sure, setSure] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const askAssistant = () =>
    suggest.mutate(undefined, {
      onSuccess: (suggestion) => {
        setReply(suggestion.body); // the admin edits it before sending
        setNote(suggestion);
      },
      onError: (error) => toast.error(error.message),
    });

  const sendReply = () =>
    send.mutate(
      { body: reply.trim() },
      {
        onSuccess: () => {
          setReply("");
          setNote(null);
          toast.success("Reply sent.");
        },
        onError: (error) => toast.error(error.message),
      },
    );

  const closeConversation = () =>
    close.mutate(undefined, {
      onSuccess: () => toast.success("The conversation is closed."),
      onError: (error) => toast.error(error.message),
    });

  return (
    <QueryBoundary query={thread}>
      {({ thread: info, report_text, messages }) => (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Report (personal details already removed)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p className="whitespace-pre-wrap">{report_text}</p>
              <Button variant="outline" size="sm" onClick={() => setShowDetails(true)}>
                Report details
              </Button>
            </CardContent>
          </Card>
          <ReportDetailsDialog
            reportId={showDetails ? reportId : null}
            onClose={() => setShowDetails(false)}
          />
          <MessageList messages={messages} viewer="admin" />

          {info.status === "closed" ? (
            <Alert>
              <AlertDescription>
                This conversation is closed. Nobody can write in it.
              </AlertDescription>
            </Alert>
          ) : (
            <>
              {info.marked_fixed && (
                <WarningAlert title="The citizen says it is fixed">
                  Close the conversation if you agree.
                </WarningAlert>
              )}
              <Field>
                <FieldLabel htmlFor="reply">Reply to the citizen</FieldLabel>
                <Textarea
                  id="reply"
                  rows={6}
                  maxLength={MAX_MESSAGE_CHARS}
                  value={reply}
                  onChange={(event) => setReply(event.target.value)}
                />
              </Field>
              {note && (
                <p className="text-sm text-muted-foreground">
                  Assistant: {note.looks_resolved ? "looks resolved" : "does not look resolved"}.{" "}
                  {note.reason} Check and edit before sending.
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                <Button disabled={send.isPending || !reply.trim()} onClick={sendReply}>
                  Send reply
                </Button>
                <Button variant="outline" disabled={suggest.isPending} onClick={askAssistant}>
                  {suggest.isPending ? "Reading the conversation…" : "Suggest reply"}
                </Button>
              </div>

              <Separator />
              <label className="flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  className="mt-1 size-4"
                  checked={sure}
                  onChange={(event) => setSure(event.target.checked)}
                />
                I want to close this conversation. Nobody can write in it afterwards.
              </label>
              <Button
                variant="destructive"
                disabled={!sure || close.isPending}
                onClick={closeConversation}
              >
                Close conversation
              </Button>
            </>
          )}
        </div>
      )}
    </QueryBoundary>
  );
};
