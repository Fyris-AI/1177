import React from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { AzureIcon , VercelIcon} from "./icons";

const ProjectOverview = () => {
  return (
    <motion.div
      className="w-full max-w-[600px] my-4"
      initial={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 5 }}
    >
      <div className="border-2 rounded-lg p-6 flex flex-col gap-4 text-sm text-muted-foreground dark:border-neutral-700 dark:bg-neutral-900">
        <p className="flex flex-row justify-center gap-4 items-center text-foreground">
          <VercelIcon />
          +
          <AzureIcon />
        </p>
        <p>
          Use the Vercel AI SDK&apos;s{" "}
          <Link
            href="https://sdk.vercel.ai/docs/reference/ai-sdk-ui/use-chat"
            className="text-blue-500"
          >
            useChat
          </Link>{" "}
          hook along with the{" "}
          <Link
            href="https://sdk.vercel.ai/docs/reference/ai-sdk-core/stream-text"
            className="text-blue-500"
          >
            streamText
          </Link>{" "}
          function to build chat applications with retrieval-augmented
          generation (RAG) capabilities, utilizing Azure AI Search for search
          functionality and Azure OpenAI for text and embedding generation.
        </p>
        <p>
          Deploy your own version of this chatbot{" "}
          <Link
            className="text-blue-500"
            href="https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FAzure-Samples%2Fazure-ai-vercel-rag-starter"
            target="_blank"
          >
            here
          </Link>
          .
        </p>
      </div>
    </motion.div>
  );
};

export default ProjectOverview;
