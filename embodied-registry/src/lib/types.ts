export type VerificationStatus = "reproduced" | "runner_verified" | "self_tested";

export type EvaluationSummary = {
  id: string;
  slug: string;
  skill: string;
  author: string;
  robot: string;
  framework: string;
  successRate: number;
  trialLabel: string;
  status: VerificationStatus;
};
