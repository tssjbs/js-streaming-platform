# Listener policies (human-facing rules)

1. **Approval required** — AI proposals do not auto-add to a playlist.
2. **Focus mode** — When enabled, filter explicit (`is_explicit=1`) tracks from ranked lists.
3. **External media** — Only allowlisted hosts may stream; unknown URLs are blocked and logged.
4. **Bias awareness** — Genre match is weighted heavily; mood mismatch is not always penalized (see model card).