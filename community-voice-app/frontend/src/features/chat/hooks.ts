import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  closeThread,
  fetchMyThreads,
  fetchThread,
  fetchThreads,
  markFixed,
  sendMessage,
  suggestReply,
  type NewMessage,
  type ThreadFilter,
} from "@/features/chat/api";
import { queryKeys } from "@/lib/query-keys";

// No push: the pages ask again every 15 seconds.
const REFRESH_MS = 15_000;

export const useThreads = (filter: ThreadFilter) =>
  useQuery({
    queryKey: queryKeys.threads(filter),
    queryFn: () => fetchThreads(filter),
    refetchInterval: REFRESH_MS,
  });

export const useMyThreads = () =>
  useQuery({
    queryKey: queryKeys.myThreads,
    queryFn: fetchMyThreads,
    refetchInterval: REFRESH_MS,
  });

export const useThread = (id: string) =>
  useQuery({
    queryKey: queryKeys.thread(id),
    queryFn: () => fetchThread(id),
    refetchInterval: REFRESH_MS,
  });

/** Runs a change on one conversation, then refreshes every chat query. */
const useThreadAction = <V>(id: string, action: (id: string, value: V) => Promise<unknown>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (value: V) => action(id, value),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.chat }),
  });
};

export const useSendMessage = (id: string) =>
  useThreadAction<NewMessage>(id, sendMessage);

export const useMarkFixed = (id: string) =>
  useThreadAction<void>(id, (threadId) => markFixed(threadId));

export const useCloseThread = (id: string) =>
  useThreadAction<void>(id, (threadId) => closeThread(threadId));

/** The suggestion is not saved on the server, so nothing needs refreshing. */
export const useSuggestReply = (id: string) =>
  useMutation({ mutationFn: () => suggestReply(id) });
