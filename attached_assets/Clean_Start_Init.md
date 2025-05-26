# EMERALD'S KILLFEED — CLEAN START & COG REPAIR PROMPT

## SINGLE TASK DIRECTIVE
This is a single-task batch operation. All phases must be executed without interruption, logging, or partial commits. Follow the instructions in order. **No output or checkpointing is permitted until the final validation passes.**

---

## PHASE 0 — CLEAN START INITIALIZATION

**Objective:** Ensure the bot environment is reset to a clean state for deterministic debugging, patching, and production startup.

### Checklist
- [ ] Remove all nested folders (e.g., `project/`, `DeadsideBot/`) and symbolic links from prior sessions
- [ ] If `.zip` or `.tar.gz` exists in `attached_assets/`, extract to root and **move contents** to project root
- [ ] Delete any duplicate, orphaned, or legacy source files to prevent namespace collision
- [ ] Ensure `.replit`, `pyproject.toml`, and runtime configs reflect correct `py-cord v2.6.1` usage
- [ ] Validate that `discord.py` is **not** present in any dependency tree
- [ ] Remove old `.env` files unless regeneration is required by logic

### Launch Command
```bash
python main.py
```

- [ ] Wait for the following confirmation in logs:
  - Gateway connection: ✅
  - Cog loading complete: ✅
  - MongoDB connection active: ✅
  - SFTP configuration verified (if used at boot): ✅
  - EmbedFactory initialized without failure: ✅

```md
# [PHASE 0] - DONE
```

---

## PHASE 1 — COG REPAIR & CONFORMANCE VALIDATION

**Objective:** Audit and repair all cogs to ensure consistent use of EmbedFactory and compliance with py-cord v2.6.1.

### Checklist
- [ ] Iterate through each cog (`*.py` in `/cogs/` or submodules)
- [ ] Ensure no `discord.py` legacy syntax is used (e.g., old command decorators or bot.add_cog patterns)
- [ ] Replace raw `discord.Embed()` usage with `EmbedFactory.build()`
- [ ] Validate that each command:
  - Renders its embed using `EmbedFactory`
  - Includes footer `Powered by Discord.gg/EmeraldServers`
  - Applies thumbnail when applicable
  - Handles errors gracefully using themed responses
- [ ] Confirm no monkey patches, no fallback embeds, and no violations of the embed consistency standard

```md
# [PHASE 1] - DONE
```

---

## RULES OF EXECUTION
- Use **py-cord 2.6.1** only — any fallback to `discord.py` is a critical error
- EmbedFactory is required for all embed output — raw embed creation is forbidden
- Do not continue to any task or phase until each phase is fully complete and verified
- This task must be completed in one atomic operation — no trial and error, no fragmentation

---

# [READY FOR NEXT PHASE]
Once Phase 1 is done, proceed to downstream features or validation immediately and atomically.
