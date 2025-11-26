"use client";

import type { JSX } from "react";
import { useMemo } from "react";
import { Smile, Meh, Frown, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Sentiment Analysis Component
 * Analyzes message sentiment and displays emotional trends
 * Uses simple lexicon-based sentiment analysis
 */

interface Message {
  content: string;
  role: string;
  createdAt: string;
}

interface SentimentAnalysisProps {
  messages: Message[];
  className?: string;
}

interface SentimentScore {
  score: number; // -1 to 1
  label: "positive" | "neutral" | "negative";
  confidence: number;
}

// Simple sentiment lexicon (expanded for better accuracy)
const positiveWords = new Set([
  "good",
  "great",
  "excellent",
  "amazing",
  "wonderful",
  "fantastic",
  "perfect",
  "love",
  "best",
  "awesome",
  "brilliant",
  "superb",
  "outstanding",
  "happy",
  "delighted",
  "satisfied",
  "pleased",
  "thank",
  "thanks",
  "appreciate",
  "helpful",
  "solved",
  "fixed",
  "resolved",
  "success",
  "beautiful",
  "nice",
]);

const negativeWords = new Set([
  "bad",
  "terrible",
  "awful",
  "horrible",
  "worst",
  "hate",
  "disappointed",
  "frustrating",
  "annoying",
  "broken",
  "issue",
  "problem",
  "error",
  "bug",
  "fail",
  "failed",
  "wrong",
  "difficult",
  "poor",
  "slow",
  "useless",
  "waste",
  "unhappy",
  "angry",
  "upset",
]);

function analyzeSentiment(text: string): SentimentScore {
  const words = text
    .toLowerCase()
    .replace(/[^\w\s]/g, "")
    .split(/\s+/);

  let positiveCount = 0;
  let negativeCount = 0;

  for (const word of words) {
    if (positiveWords.has(word)) {
      positiveCount++;
    }
    if (negativeWords.has(word)) {
      negativeCount++;
    }
  }

  const total = positiveCount + negativeCount;
  if (total === 0) {
    return { score: 0, label: "neutral", confidence: 0 };
  }

  const score = (positiveCount - negativeCount) / total;
  const confidence = total / words.length;

  let label: "positive" | "neutral" | "negative";
  if (score > 0.2) {
    label = "positive";
  } else if (score < -0.2) {
    label = "negative";
  } else {
    label = "neutral";
  }

  return { score, label, confidence };
}

export function SentimentAnalysis({
  messages,
  className,
}: SentimentAnalysisProps): JSX.Element {
  const analysis = useMemo(() => {
    const userMessages = messages.filter((m) => m.role === "USER");
    const assistantMessages = messages.filter((m) => m.role === "ASSISTANT");

    const userSentiments = userMessages.map((m) => analyzeSentiment(m.content));
    const assistantSentiments = assistantMessages.map((m) =>
      analyzeSentiment(m.content)
    );

    const avgUserScore =
      userSentiments.reduce((sum, s) => sum + s.score, 0) /
      (userSentiments.length || 1);

    const avgAssistantScore =
      assistantSentiments.reduce((sum, s) => sum + s.score, 0) /
      (assistantSentiments.length || 1);

    // Sentiment distribution
    const distribution = {
      positive: userSentiments.filter((s) => s.label === "positive").length,
      neutral: userSentiments.filter((s) => s.label === "neutral").length,
      negative: userSentiments.filter((s) => s.label === "negative").length,
    };

    // Sentiment trend (comparing first half vs second half)
    const midpoint = Math.floor(userSentiments.length / 2);
    const firstHalfAvg =
      userSentiments
        .slice(0, midpoint)
        .reduce((sum, s) => sum + s.score, 0) / (midpoint || 1);
    const secondHalfAvg =
      userSentiments
        .slice(midpoint)
        .reduce((sum, s) => sum + s.score, 0) /
      (userSentiments.length - midpoint || 1);
    const trend = secondHalfAvg - firstHalfAvg;

    return {
      avgUserScore,
      avgAssistantScore,
      distribution,
      trend,
      total: userMessages.length,
    };
  }, [messages]);

  const getSentimentColor = (score: number) => {
    if (score > 0.2) {
      return "text-green-500";
    }
    if (score < -0.2) {
      return "text-red-500";
    }
    return "text-yellow-500";
  };

  const getSentimentIcon = (score: number) => {
    if (score > 0.2) {
      return Smile;
    }
    if (score < -0.2) {
      return Frown;
    }
    return Meh;
  };

  const UserIcon = getSentimentIcon(analysis.avgUserScore);
  const AssistantIcon = getSentimentIcon(analysis.avgAssistantScore);

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-surface p-6",
        className
      )}
    >
      <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
        <Smile className="h-5 w-5" />
        Sentiment Analysis
      </h3>

      {/* Average Sentiment Scores */}
      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border p-4">
          <p className="mb-2 text-sm text-foreground-secondary">
            Customer Sentiment
          </p>
          <div className="flex items-center gap-3">
            <UserIcon
              className={cn("h-8 w-8", getSentimentColor(analysis.avgUserScore))}
            />
            <div>
              <p className="text-2xl font-bold">
                {(analysis.avgUserScore * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-foreground-secondary">
                {analysis.avgUserScore > 0.2
                  ? "Positive"
                  : analysis.avgUserScore < -0.2
                    ? "Negative"
                    : "Neutral"}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-border p-4">
          <p className="mb-2 text-sm text-foreground-secondary">
            Assistant Tone
          </p>
          <div className="flex items-center gap-3">
            <AssistantIcon
              className={cn(
                "h-8 w-8",
                getSentimentColor(analysis.avgAssistantScore)
              )}
            />
            <div>
              <p className="text-2xl font-bold">
                {(analysis.avgAssistantScore * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-foreground-secondary">
                {analysis.avgAssistantScore > 0.2
                  ? "Positive"
                  : analysis.avgAssistantScore < -0.2
                    ? "Negative"
                    : "Neutral"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Sentiment Distribution */}
      <div className="mb-6">
        <p className="mb-3 text-sm font-medium">Sentiment Distribution</p>
        <div className="space-y-2">
          {/* Positive */}
          <div className="flex items-center gap-3">
            <Smile className="h-4 w-4 text-green-500" />
            <div className="flex-1">
              <div className="h-2 overflow-hidden rounded-full bg-background">
                <div
                  className="h-full bg-green-500"
                  style={{
                    width: `${(analysis.distribution.positive / analysis.total) * 100}%`,
                  }}
                />
              </div>
            </div>
            <span className="text-sm font-medium">
              {analysis.distribution.positive}
            </span>
          </div>

          {/* Neutral */}
          <div className="flex items-center gap-3">
            <Meh className="h-4 w-4 text-yellow-500" />
            <div className="flex-1">
              <div className="h-2 overflow-hidden rounded-full bg-background">
                <div
                  className="h-full bg-yellow-500"
                  style={{
                    width: `${(analysis.distribution.neutral / analysis.total) * 100}%`,
                  }}
                />
              </div>
            </div>
            <span className="text-sm font-medium">
              {analysis.distribution.neutral}
            </span>
          </div>

          {/* Negative */}
          <div className="flex items-center gap-3">
            <Frown className="h-4 w-4 text-red-500" />
            <div className="flex-1">
              <div className="h-2 overflow-hidden rounded-full bg-background">
                <div
                  className="h-full bg-red-500"
                  style={{
                    width: `${(analysis.distribution.negative / analysis.total) * 100}%`,
                  }}
                />
              </div>
            </div>
            <span className="text-sm font-medium">
              {analysis.distribution.negative}
            </span>
          </div>
        </div>
      </div>

      {/* Sentiment Trend */}
      <div className="rounded-lg border border-border bg-background p-4">
        <p className="mb-2 text-sm font-medium">Conversation Trend</p>
        <div className="flex items-center gap-3">
          {analysis.trend > 0.1 ? (
            <>
              <TrendingUp className="h-6 w-6 text-green-500" />
              <div>
                <p className="text-sm font-medium text-green-500">
                  Improving
                </p>
                <p className="text-xs text-foreground-secondary">
                  Customer sentiment is getting better
                </p>
              </div>
            </>
          ) : analysis.trend < -0.1 ? (
            <>
              <TrendingDown className="h-6 w-6 text-red-500" />
              <div>
                <p className="text-sm font-medium text-red-500">Declining</p>
                <p className="text-xs text-foreground-secondary">
                  Customer sentiment is getting worse
                </p>
              </div>
            </>
          ) : (
            <>
              <Meh className="h-6 w-6 text-yellow-500" />
              <div>
                <p className="text-sm font-medium text-yellow-500">Stable</p>
                <p className="text-xs text-foreground-secondary">
                  Customer sentiment is consistent
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
