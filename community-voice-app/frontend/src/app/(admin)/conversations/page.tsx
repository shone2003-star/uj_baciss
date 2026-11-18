import type { Metadata } from "next";

import { ConversationsScreen } from "@/features/chat/components/conversations-screen";

export const metadata: Metadata = { title: "Conversations" };

const ConversationsPage = () => {
  return <ConversationsScreen />;
};

export default ConversationsPage;
