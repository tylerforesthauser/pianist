# Planning Documents

This directory contains the core planning documents for the Pianist project. These documents should be reviewed and revised throughout the project lifecycle.

## Documents

### [MISSION.md](MISSION.md)
**Purpose:** Defines the mission, core goals, current state assessment, and success criteria.

**Contents:**
- Mission statement
- Core goal and vision
- Current state assessment (75% achievement)
- Critical gaps analysis
- Success criteria
- Principles and target users

**When to update:**
- When goals change
- After major milestones
- When reassessing current state

---

### [ROADMAP.md](ROADMAP.md)
**Purpose:** Outlines the feature priorities, implementation roadmap, technical approach, and getting started guide. **This is the single source of truth for project status and planning.**

**Contents:**
- **Current Status** (consolidated status assessment - update this, don't create new status docs)
- Feature priorities (6 main areas)
- Implementation roadmap (3 phases)
- Technical approach and design
- Example workflows
- Success metrics
- Getting started guide (implementation steps, dependencies, testing)
- Open questions

**When to update:**
- **Always update the "Current Status" section** when making status assessments
- When priorities change
- After completing phases or features
- When technical approach changes
- When new questions are answered
- When implementation steps change
- **DO NOT create separate status documents** - consolidate everything in ROADMAP.md

---

---

## Document Maintenance

**Principles:**
- Keep documents focused and up-to-date
- **Don't create new documents without clear need** - Carefully consider if a new document is truly required
- **ROADMAP.md is the single source of truth for status** - Always update the "Current Status" section there, never create separate status documents
- **Temporary documents** should go in `docs/temp/` - Use this for work-in-progress, research notes, or documents that will be consolidated/removed later
- Consolidate related information
- Remove outdated information
- Update based on learnings and feedback

**Review Schedule:**
- After each phase completion
- Quarterly reviews
- When major decisions are made
- When goals or priorities change
- Periodically clean up `docs/temp/` directory

---

## Related Documents

- **[README.md](README.md)** - User-facing documentation
- **[AI_PROMPTING_GUIDE.md](AI_PROMPTING_GUIDE.md)** - AI prompting guidance
- **[docs/](docs/)** - Technical documentation
- **[docs/temp/](docs/temp/)** - Temporary documents (work-in-progress, research notes, etc.)

