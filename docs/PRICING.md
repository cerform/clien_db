# Pricing modifiers and markups (Israel)

This document explains price modifiers (markups/fees) used by the project and seeded into the database.

## What are pricing modifiers

A `pricing_modifier` is an entity that represents a fixed fee or percentage-based surcharge/discount that can be applied to a service price. They are stored in the `pricing_modifiers` table and linked to services via `service_pricing_modifiers`.

## Typical modifiers seeded by `scripts/seed_services.py`

- WEEKEND_10 — Weekend surcharge, percent 10% (common for weekend appointments).
- RUSH_25 — Rush / short-notice surcharge, percent 25%.
- SENIOR_30 — Senior artist premium, percent 30% (experienced artists charge higher rates).
- COLOR_15 — Color surcharge, percent 15% (color work can need more time/inks).
- DEPOSIT_250 — Standard deposit (non-refundable), fixed 250 ILS.
- SKETCH_credited — Sketch/design fee (credited at payment), fixed 400 ILS.

## How to apply modifiers

Modifiers are linked to services in `service_pricing_modifiers`. Application logic (e.g., during booking or checkout) is intentionally left to business logic: apply percent modifiers multiplicatively on top of base price, and add fixed modifiers as absolute additions or credits depending on modifier semantics.

## Notes

- Prices in the default `SERVICES` seed are expressed in Israeli New Shekels (₪ / ILS) and represent approximate ranges found in Israeli studios (mini/medium/large projects, hourly rates).
- The migration `db/migrations/sql/007_create_pricing_modifiers.sql` creates the modifiers tables. Run migrations before running the seed script to enable modifier seeding.
