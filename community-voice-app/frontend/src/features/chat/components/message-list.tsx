import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Message } from "@/features/chat/schemas";

const NAMES = { citizen: "Citizen", admin: "Municipality" } as const;

/**
 * The messages of a conversation. React shows `body` as plain text, so a message
 * can never become a link or markup.
 */
export const MessageList = ({
  messages,
  viewer,
}: {
  messages: Message[];
  viewer: Message["sender"];
}) => {
  return (
    <ul className="flex flex-col gap-2" aria-label="Messages">
      {messages.map((message) => {
        const mine = message.sender === viewer;
        return (
          <li
            key={message.id}
            className={cn(
              "max-w-[85%] rounded-lg border p-3 text-sm",
              mine ? "self-end bg-primary/10" : "self-start bg-muted",
            )}
          >
            <p className="mb-1 text-xs text-muted-foreground">
              {mine ? "You" : NAMES[message.sender]} · {formatDateTime(message.created_at)}
            </p>
            <p className="whitespace-pre-wrap">{message.body}</p>
          </li>
        );
      })}
    </ul>
  );
};
