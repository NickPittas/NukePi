# Using Nuke Pi

Open **Pane > Nuke Pi**. See [INSTALLATION.md](INSTALLATION.md) first.

## Accounts, models and defaults

- **Pi accounts…** — add API-key or subscription/OAuth accounts for any provider in the pinned Pi SDK catalog. Credentials live in Pi's private store, never in QSettings, chat or logs. **Check** verifies locally; **Logout** is local only.
- **Manage models…** — check the models for the picker and Pi's model cycling, then pick an explicit **Default model** among them. Stored in Pi's private `settings.json` (`enabledModels`, `defaultProvider`, `defaultModel`). Select all stores the current explicit IDs, not future ones.
- Fresh conversations use the default. A continued conversation keeps its actual model; if that model is no longer allowed you must choose explicitly, it is never silently replaced.
- Send stays disabled until the session is restored, the model and effort are acknowledged by Pi, and the Nuke tools are confirmed ready. The effort you selected is kept across automatic continue and New Chat and is checked against what Pi actually reports; a mismatch keeps Send blocked and shows an error. The panel does not silently retry or fall back to another effort.

## Conversations

- **Automatic continue.** Opening a script restores its previous conversation without a prompt.
- **New Chat** archives the transcript and starts a fresh process and session.
- **Busy Send / `/btw`** steers the same session safely (manual only); Cancel stops the run.
- The context bar shows context-window usage; hover for details.

## Chat display

- Markdown renders fully: headings, lists, tables, quotes, links, code fences.
- Each tool call is a separate collapsible bubble (title, status, elapsed time, formatted arguments and results, errors); thinking is collapsible; delivered images appear inline in chronological order.
- The view follows new output while you are at the bottom and keeps your place when you scroll up.
- **A-**, **A+** and reset change chat text size (8–24, default 11), saved as `chat/font_size`.
- The theme applies to the Nuke Pi panel and its dialogs only, never to Nuke.

## Questions from the agent

When the agent is missing expertise or needs a decision, it asks and then waits; there is no timeout.

- **Option buttons** — click one to answer.
- **Checkboxes** — when several answers can apply, tick at least one, then confirm; **Answer** stays disabled until something is ticked. An empty selection is not possible: use **Stop here** (if offered) or **Cancel (stops the run)** instead.
- **Your own answer** — if the question offers a custom-response option, click it first; only then does the normal message box enable. Type your text and press **Answer**. This answers the question; it does not start a new chat turn.
- **Optional comment** — after you make a selection, some questions then ask for a short note. It may be left empty.
- **Cancel (stops the run)** — stops the agent. It does not pick a default answer.
- **After a finished composite** — once the graph holds a complete composite (built in this chat, or loaded from a file) and the agent has rendered it, it must ask which remaining issues to fix, listing them as options plus **Stop here**. Any answer other than **Stop here** lets it make changes again; the agent is told to work on the issue you picked, but Nuke does not enforce that. **Stop here** ends its work with a short summary and keeps further scene changes blocked until you send your next message.

The question dialog comes from the pinned `pi-ask-user` 0.17.1 (MIT), installed with the private runtime by the normal installer; nothing is taken from global Pi or Node. Verified on Linux x64 only.

## Nuke tools

The agent uses ordinary authorized Python (`execute_python`) plus optional `nuke_action`, `nuke_workflow`, `get_nuke_context`, `capture_nuke_screenshot`, and read-only knowledge/API-documentation tools. Python runs in Nuke, is not an OS sandbox, and asks for confirmation unless **Trusted Python session** is enabled (only for the sole visible checked pane; hiding or closing revokes it). See the README for details.

## Verification status

Linux x64 is the only natively verified platform. Windows and macOS behavior is implemented but not natively verified.
