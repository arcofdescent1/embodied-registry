import { demoEvaluations } from "./demo-data";
import { getPublicSupabaseClient } from "./supabase/server";
import type { EvaluationSummary, VerificationStatus } from "./types";

type EvaluationRow = {
  id: string; slug: string; skill_name: string; author_name: string; robot_family: string;
  framework: string; success_rate: number; trial_count: number; reproduction_count: number;
  verification_status: VerificationStatus;
};

export async function listEvaluations(): Promise<{ evaluations: EvaluationSummary[]; demo: boolean }> {
  const supabase = getPublicSupabaseClient();
  if (!supabase) return { evaluations: demoEvaluations, demo: true };

  const { data, error } = await supabase
    .from("evaluation_summaries")
    .select("id,slug,skill_name,author_name,robot_family,framework,success_rate,trial_count,reproduction_count,verification_status")
    .order("published_at", { ascending: false })
    .limit(30);

  if (error || !data?.length) return { evaluations: demoEvaluations, demo: true };
  return {
    demo: false,
    evaluations: (data as EvaluationRow[]).map((row) => ({
      id: row.id, slug: row.slug, skill: row.skill_name, author: row.author_name,
      robot: row.robot_family, framework: row.framework, successRate: row.success_rate,
      trialLabel: row.reproduction_count > 1 ? `${row.reproduction_count} reproductions` : `${row.trial_count} trials`,
      status: row.verification_status,
    })),
  };
}
