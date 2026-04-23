"use client";

import ChatPane from "@/components/ChatPane";
import UploadPane from "@/components/UploadPane";
import { useChatStream } from "@/hooks/useChatStream";
import { useContractUpload } from "@/hooks/useContractUpload";
import { useThreadId } from "@/hooks/useThreadId";
import { useUploadedDocuments } from "@/hooks/useUploadedDocuments";

export default function Home() {
  const threadId = useThreadId();
  const { documents, addDocument, removeDocument } = useUploadedDocuments();
  const {
    messages,
    isStreaming,
    streamError,
    currentToolCall,
    sendMessage,
    clearConversation,
  } = useChatStream(threadId);

  const { uploadFile, isUploading, uploadError } = useContractUpload({
    onUploadSuccess: addDocument,
  });

  return (
    <main className="app-shell">
      <div className="ambient-gradient" />
      <div className="ambient-grid" />

      <UploadPane
        documents={documents}
        isUploading={isUploading}
        uploadError={uploadError}
        onUploadFile={uploadFile}
        onRemoveDocument={removeDocument}
      />

      <ChatPane
        messages={messages}
        isStreaming={isStreaming}
        streamError={streamError}
        currentToolCall={currentToolCall}
        threadId={threadId}
        onSendMessage={sendMessage}
        onClearConversation={clearConversation}
      />
    </main>
  );
}
