---
name: magnific
description: >-
  Use this skill for any AI media creation or enhancement task handled by
  Magnific AI (the `mcp__Magnific__*` tools): upscaling or enhancing images and
  video, generating images/video/3D/audio, editing images (crop, resize, expand,
  relight, remove/replace background, restyle, reimagine, retouch, skin enhance),
  depth/PBR maps, text-to-speech, music and sound effects, dubbing, and managing
  creations, folders, tags, spaces and flows. Trigger on requests like "upscale
  this image", "make it HDR", "generate an image/video", "enhance the skin",
  "remove the background", "dub this video", "turn this into 3D", or "read it
  aloud". Requires the Magnific MCP server to be connected.
---

# Magnific AI

Magnific AI is a full media-generation and enhancement platform exposed through
the `mcp__Magnific__*` MCP tools. This skill covers how to drive those tools
correctly. It is **not** a substitute for the tools' own descriptions — read the
relevant `*_list` / `*_models_list` tool before a generation call to pick modes
and parameters.

## Connection

The server is reached over HTTP MCP. To add it to a local Claude Code install:

```bash
claude mcp add --transport http magnific https://mcp.magnific.com
```

In this cloud environment the server is already configured; the tools appear as
`mcp__Magnific__*`. Verify with `account_profile` or `account_balance`. Most
generation/enhancement tools **cost credits** — check `account_balance` (or
`simulate_cost`) before running expensive batches, and never regenerate a
creation that is already queued.

## Golden rules (from the server's agent relay)

1. **Follow the `instruction` field.** Every tool response may include an
   `instruction` field (or error text) telling you what to do with the payload.
   Do what it says.
2. **Confirm before replying.** After any generation or media-processing tool
   (`images_*`, `video_*`, `models3d_*`, `audio_*`), call `creations_show`
   (1–8 identifiers, inline preview) and then `creations_wait` to confirm the
   result and obtain the final asset URL before you tell the user it is done.
   For text-only surfaces share the `webUrl` instead.
3. **Chain by identifier, never by `webUrl`.** When feeding one creation into
   another tool (e.g. image → `video_generate` keyframes/references), pass the
   creation `identifier` (or the `url` from `creations_get`/`creations_wait`),
   not the `webUrl`.
4. **Upload inputs first.** Operations act on a `creationIdentifier`, not a raw
   file. Import inputs before editing (see *Getting an image in*).
5. **Speak in plain terms.** When writing to the user, use names, titles,
   `webUrl`, and descriptions. Never quote internal identifiers, UUIDs, folder
   references, or request ids unless the user explicitly asks — those are for
   your next tool call only.
6. **Only call tools that exist** in your current tool list. If the server's
   instructions name a tool you don't have, it isn't available to you.

## Getting an image in (upload)

- **Public URL** → `creations_upload_image` (one step).
- **Local / user-provided file** → `creations_request_upload`, then
  `creations_finalize_upload`. Inspect with `creations_upload_show`.
- **Stock asset** → `stock_search` → `stock_to_creation`.

Every edit/upscale tool then takes the resulting `creationIdentifier`.

## Choosing the right tool

**Images — enhance / upscale**
- `images_upscale` — AI upscale 2x–16x for sharpness/detail. Call
  `images_upscale_modes_list` first to pick a `mode` and its params; defaults are
  `mode=creative, scale=2x`. Saved presets: `images_upscale_presets_list`.
- `images_skin_enhancer` — skin/portrait enhancement (`faithful` keeps identity,
  `creative` reinterprets, `flexible` uses presets).
- `images_retouch` (see `retouch_models_list`), `images_relight`.

**Images — resize / reframe** (distinct operations, don't mix them up)
- Exact pixels → `images_resize`.
- Aspect-ratio crop → `images_crop` (`auto=true` for AI focal-point crop).
- Extend canvas / outpaint → `images_expand`.

**Images — generate / transform**
- `images_generate` (read `images_models_list` / `images_models_settings` /
  `images_models_show` first), `images_variations`, `images_reimagine`,
  `images_restyle`, `images_change_camera`.
- Background: `images_remove_background`, `images_replace_background`.
- Vector/SVG: `images_to_svg`, `images_generate_svg`, `images_animate_svg`.
- Maps for 3D/control: `images_depth_map`, `images_pbr_maps`, `images_segment`,
  `images_split_grid`.

**Video**
- Generate → `video_generate` (read `video_models_list`).
- Upscale → `video_upscale` (read `video_upscale_models_list`; Topaz or Magnific).
- **HDR / Hyperion / "make it HDR"** → `video_hdr`, **never** `video_upscale`.
- Edit: `video_cut`, `video_crop`, `video_zoom`, `video_extend`,
  `video_concatenate`, `video_speed`, `video_color_grade`, `video_relight`,
  `video_remove_background`, `video_vfx` (`video_vfx_list`), `video_modify`.
- Audio on video: `video_dubbing` (see below), `video_speak`, `video_music`,
  `video_soundfx`, `video_extract_audio`, `video_audio_mix`.

**Dubbing / translating / subtitling a video**
- Prefer `video_dubbing` — it opens the studio (options → free preview of the
  lines → edits → confirm). **Nothing is charged until the user confirms there.**
- Only when the client cannot render the studio:
  `video_dubbing_preview` → `video_dubbing_preview_get` → `video_dubbing_confirm`.

**3D** — `models3d_generate` / `models3d_text_generate`, then `models3d_remesh`,
`models3d_retexture`, `models3d_rig`, `models3d_animate`, `models3d_segment`,
`models3d_complete`.

**Audio** — `audio_tts` (+ `audio_tts_direction`; voices via `audio_voices_list`
/ `audio_voices_show`), `audio_music_generate`, `audio_sfx_generate`,
`audio_isolate`, `audio_voice_change`.

## Organizing work

- **Folders / projects**: `folders_list`, `folders_create`, `projects_move`.
  `folderReference` does **not** persist — once the user names a target folder,
  pass it on **every** later generation/edit call.
- **Creations**: `creations_list`, `creations_search` (data-only — follow with
  `creations_show` to let the user browse inline), `creations_get`,
  `creations_move`, `creations_like`, `creations_comment`, `creations_deliver`,
  `creations_register_download`, `creation_status`.
- **Tags**: `tags_list`, `tags_create`, `tags_assign`, `tags_unassign`.
- **Spaces / flows** (multi-step pipelines): `spaces_*`, `flows_*`. Estimate
  cost with `simulate_flows` / `simulate_spaces` before running.

## Typical end-to-end flow

1. Get the input in (`creations_upload_image` or request/finalize upload).
2. If unsure of parameters, read the matching `*_list` / `*_models_list` tool.
3. Optionally `simulate_cost` for pricey jobs; confirm credits.
4. Run the operation (e.g. `images_upscale`), passing the `creationIdentifier`
   and, if the user chose one, the `folderReference`.
5. `creations_show` for an inline preview, then `creations_wait` to confirm.
6. Report back with the human-readable name / `webUrl` — not internal ids.
