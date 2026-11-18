import type { Metadata } from "next";

import { MessagesScreen } from "@/features/chat/components/messages-screen";

export const metadata: Metadata = { title: "Messages" };

const MessagesPage = () => {
  return <MessagesScreen />;
};

export default MessagesPage;
