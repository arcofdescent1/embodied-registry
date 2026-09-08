import { listEvaluations } from "@/lib/evaluations";
import { RegistryClient } from "./registry-client";

export default async function Home() {
  const { evaluations, demo } = await listEvaluations();
  return <RegistryClient evaluations={evaluations} demo={demo} />;
}
