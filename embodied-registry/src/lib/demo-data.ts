import type { EvaluationSummary } from "./types";

export const demoEvaluations: EvaluationSummary[] = [
  { id: "demo-cable", slug: "bimanual-cable-routing", skill: "Bimanual cable routing", author: "Atlas Lab", robot: "ALOHA 2", framework: "LeRobot · ACT", successRate: 91.2, trialLabel: "3 reproductions", status: "reproduced" },
  { id: "demo-package", slug: "deformable-package-pick", skill: "Deformable package pick", author: "Open Manipulation", robot: "SO-101", framework: "LeRobot · SmolVLA", successRate: 87, trialLabel: "100 trials", status: "runner_verified" },
  { id: "demo-drawer", slug: "drawer-object-retrieve", skill: "Drawer open + object retrieve", author: "Northstar Robotics", robot: "Franka FR3", framework: "ROS 2 · Diffusion", successRate: 78.6, trialLabel: "2 reproductions", status: "self_tested" },
];
