import { toast } from "sonner";

import { QueryBoundary } from "@/components/shared/query-boundary";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { CitizenComposer } from "@/features/chat/components/citizen-composer";
import { MessageList } from "@/features/chat/components/message-list";
import { useMarkFixed, useThread } from "@/features/chat/hooks";

/** One conversation, as the citizen sees it. */
export const CitizenConversation = ({ reportId }: { reportId: string }) => {
  const thread = useThread(reportId);
  const fixed = useMarkFixed(reportId);

  return (
    <QueryBoundary query={thread}>
      {({ thread: info, messages }) => (
        <div className="space-y-4">
          <MessageList messages={messages} viewer="citizen" />
          {info.status === "closed" ? (
            <Alert>
              <AlertDescription>
                The municipality closed this conversation. You can still read it.
              </AlertDescription>
            </Alert>
          ) : (
            <>
              {info.marked_fixed ? (
                <Alert>
                  <AlertDescription>
                    You said this is fixed. The municipality will close the conversation.
                  </AlertDescription>
                </Alert>
              ) : (
                <Button
                  variant="outline"
                  disabled={fixed.isPending}
                  onClick={() =>
                    fixed.mutate(undefined, { onError: (error) => toast.error(error.message) })
                  }
                >
                  Mark as fixed
                </Button>
              )}
              <CitizenComposer reportId={reportId} />
            </>
          )}
        </div>
      )}
    </QueryBoundary>
  );
};
