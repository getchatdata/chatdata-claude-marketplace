---
description: Publish one reviewed ChatData pending patch through the MCP hub.
---

# Publish Patch

Use this command only after the user has reviewed and approved a pending ChatData patch.

First use the ChatData MCP server and run `chatdata_doctor`.

- If the tool is unavailable, stop and say: "ChatData MCP is not connected. Install or repair the MCP from ChatData Settings, then rerun `/chatdata:publish-patch`."
- If `chatdata_doctor` reports config, consent, or hub errors, stop and show the exact failing check plus the next install/repair command.
- If healthy, continue.

Then use the ChatData MCP server and run `chatdata_list_review_queue`.

- If the user supplied a patch id, find that exact patch and summarize the path, type, owner, and content preview before publishing.
- If the user did not supply a patch id, list the pending patches and ask which one to publish. Do not guess.
- If there are no pending patches, say the review queue is empty and stop.

After explicit approval for a specific patch id, use the ChatData MCP server and run `chatdata_publish_patch` with that `patch_id`.

Required output:

- MCP doctor status
- patch id
- path and review state before publishing
- publish result
- local cache refresh status
- next verification command: `/chatdata:audit-context`
