# Event counting design

The product episode graph below remains a proposed extension. Current events include
placed/transferred/removed/disappeared, person-zone transitions and now conservative
directional person_entered/person_exited events. See the [implemented ontology](../annotation_guidelines.md).
Product movements must not be relabeled as preparation
or handover without new evidence and annotations.

Keep three layers: observed detections/track fragments, inferred temporal events,
and POS-confirmed quantities. Use anonymous session-local identities. An event
stores camera, capture interval, source frame/clip references, calibration/model
version, logical item episode, contributing track fragments, uncertainty and review
status. Evidence references must survive optional JPEG expiry through source hashes.

## Partial state graph

    unknown -> preparation_observed -> ready_observed -> awaiting_pickup
    awaiting_pickup -> handover_observed | pickup_unassigned | returned | unknown

These are allowed partial paths, not a forced sequence. Observation can begin at
ready or pickup; occlusion is not a handover. Returned/discarded requires observable
evidence. A closed cup alone does not identify the drink, its completion or payment.
Person proximity alone does not identify the recipient or their role.

Preparation should require an annotated, visible action/transition at a preparation
station. Handover should require a product leaving pickup with temporally consistent
person-product interaction evidence. Ambiguous simultaneous interactions remain
pickup_unassigned or unknown. Drink/SKU subtypes need distinguishable visual evidence.

## Identity and idempotency

- A tracker ID is a fragment, not a unique physical product or prepared drink.
- Maintain a logical item episode with conservative evidence-linked fragments.
  Time/space/appearance compatibility can propose a merge, but uncertain reappearance
  must not automatically create a second completed handover or force a merge.
- A reusable cup can participate in multiple preparation episodes. Counting unique
  physical cups for a whole day would undercount drinks; existing one-sale-per-track
  logic needs a validated episode policy before representing this case.
- Identify a candidate once and persist its identity before review/retry. Count one
  finalized event per episode and transition; corrections append a new version that
  updates the derived count, preserving history.
- Replaying the same source/config/run deduplicates records. New run IDs or a tracker
  reset do not, by themselves, establish a new customer visit or product episode.
- One order with several cups can have several episodes; paid quantity conservation
  still applies. Neither a handover nor a model review establishes a paid transaction.

## Cases that must be labeled and tested

| Case | Required behavior |
|---|---|
| Cup stationary for minutes | No repeated preparation/handover count |
| Two cups moved together | Preserve two items if separately visible; otherwise uncertain multiplicity |
| Cup behind barista, reappears | Preserve or review identity; do not count disappearance as handover |
| Product picked up and replaced | Return/uncertain transition, not a second completed unit by default |
| Several people reach at once | Unknown recipient when association is ambiguous |
| Staff restocking | Differentiate observable placement from service; staff role is not appearance-based proof |
| Seated person temporarily hidden | Temporarily unobserved/unknown, evaluate timeout against ground truth |
| Standing person near table | Require calibrated seat evidence; do not assert seating from generic proximity |
| Decoder outage / scene shift | Mark gap; invalidate unsupported transitions, then recover explicitly |
| Restart / repeated VLM request | One persisted candidate/result identity; transactional deduplication |
| Refund or later POS revision | Correct paid ledger independently; preserve visual observation |

VLM output is advisory: event proposal, visible supporting frame references and
unknown/abstain are schema-validated. A clip must show temporal evidence. Store raw
review provenance and apply the same event gates/human review. Do not add a state
called paid, theft or satisfaction inferred from a video model.
