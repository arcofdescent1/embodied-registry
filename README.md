# Embodied Registry

Embodied Registry makes robot-policy transfer a testable claim.

We help developers using low-cost, LeRobot-compatible manipulation arms determine whether a published policy can run on their hardware—and understand why when it cannot.

## Phase 0 focus

The initial community is practitioners actively attempting to reproduce or adapt public manipulation policies on SO-100, SO-101, and closely compatible low-cost LeRobot hardware. The first measurable problem is the time and uncertainty involved in reconstructing artifact, calibration, sensing, action, runtime, and evaluation conditions.

Read the complete [project thesis](https://embodied-registry.vercel.app/thesis).

## Participate in Phase 1

- [Share a policy-transfer experience](https://github.com/arcofdescent1/embodied-registry/issues/new?template=problem-conversation.yml)
- [Apply as a founding design partner](https://github.com/arcofdescent1/embodied-registry/issues/new?template=design-partner.yml)
- [Read and challenge the field notes](https://embodied-registry.vercel.app/field-notes)
- [Join the public discussion](https://github.com/arcofdescent1/embodied-registry/discussions)

The first discovery cycle consists of 25 problem conversations and five concrete design-partner commitments. Public issue forms must not contain confidential information, credentials, personal contact information, private datasets, or safety-sensitive operational details.

## Evidence policy

Direct observation, participant reports, and project inference are distinguished. Failed reproductions are evidence. “Reproduced” means an evaluator independent of the artifact owner obtained a comparable result under a declared protocol.

## Repository layout

- `embodied-registry/` — Next.js application deployed on Vercel
- `embodied-registry/schema/` — open robot-skill manifest schema and example
- `embodied-registry/supabase/` — production database migration prepared for Phase 2
- `.github/ISSUE_TEMPLATE/` — Phase 1 interview and design-partner intake
