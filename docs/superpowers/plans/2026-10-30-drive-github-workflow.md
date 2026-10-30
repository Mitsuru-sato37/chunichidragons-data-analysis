# Drive/GitHub Workflow Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make repository workflow rules, video candidate lookup, and resumable task history discoverable in GitHub while keeping Drive documents and deliverables in Drive.

**Architecture:** Use the existing `docs/repository_workflow.md` for repository-wide storage and closeout rules, `AGENTS.md` as the entry point, a Chunichi-specific candidate workflow and index, and `docs/STATUS.md` for resumable work state. Do not duplicate full Drive documents or alter unrelated dirty work.

**Tech Stack:** Markdown documentation; Git; Google Drive links.

**Spec:** User-provided attachment `貼り付けたテキスト.txt` and the current conversation's clarified policy.

## Global Constraints

- GitHub stores repository rules, procedures, and concise handoff history.
- Google Drive stores idea memos, research, source materials, and completed deliverables.
- Drive and GitHub do not automatically sync; record verified Drive links in GitHub.
- Preserve all unrelated working-tree changes.
- After `お疲れ` closeout, ask before archiving the conversation.

## Review Focus

- Existing repository docs named in the attachment do not exist; adapt to files that do.
- Candidate index must link to the verified Drive memo and `#00動画` folder.
- Keep the existing unrelated video production plan change untouched.
- Do not push or commit without the user's explicit closeout authorization.

---

### Task 1: Link repository instructions to the established workflow

**Files:** Modify `AGENTS.md`; create `docs/drive_github_workflow.md` for Chunichi-specific locations.

- [x] Point idea lookup to the candidate index and delegate repository-wide rules to `docs/repository_workflow.md`.

### Task 2: Make the current candidate discoverable

**Files:** Create `docs/video_idea_index.md`.

- [x] Add the current Chunichi roster-space idea as a candidate with its Drive memo and folder links.

### Task 3: Record resumable status and verify

**Files:** Create `docs/STATUS.md` and this plan.

- [x] Check Markdown links, intended file list, and whitespace errors; report uncommitted status.
