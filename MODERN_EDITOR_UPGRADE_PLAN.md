# Lylis Modern Editor Upgrade Plan

## Existing architecture to preserve

| Existing module | Reusable responsibility | Target component role |
| --- | --- | --- |
| `gui/main_window.py` | Project orchestration, signals, autosave, shortcuts | `EditorShell`, `TopToolbar`, `TransportControls` |
| `gui/tabs/media_tab.py` | Media/audio upload, multi-song album, audio tools | `AssetPanel`, `AudioEditor` |
| `gui/preview_widget.py` | Rendering, object selection/drag, overlay persistence | `PreviewCanvas` |
| `gui/inspector_panel.py` | Contextual object/text properties | `InspectorPanel` |
| `gui/timeline_widget.py` | Multi-track drawing, trims, split, snap, waveform, playhead | `Timeline`, `TimelineTrack`, `TimelineClip`, `Playhead` |
| `gui/tabs/lyrics_tab.py` | LRC/SRT/ASS workflows and timing | `LyricsEditor`, `Captions` |
| `gui/tabs/effects_tab.py` | Effects, filters, adjustments | `EffectsBrowser` |
| `gui/tabs/transitions_tab.py` | Transition selection/application | `TransitionBrowser` |
| `gui/tabs/templates_tab.py` | Editable style/template presets | `Templates` |
| `core/project_model.py` | Central serializable editing state | Central editor state |
| `core/undo_manager.py` | Snapshot undo/redo | Command-history migration base |
| `gui/export_dialog.py` | Threaded export and cancellation | `ExportDialog` |

## Important gaps found

- The checkout has no Teacher or Questions source module, although those features were described as existing. Their data must not be guessed or discarded; integration should happen when those modules/data are available.
- Several legacy panels use local light QSS. Phase 1 maps those tokens into the shared dark editor theme while leaving their behavior intact.
- The timeline has seven specialized layers, not a generic track/clip model yet. Generic track operations should be introduced through adapters before the persisted project schema changes.
- Undo/redo is snapshot-based. A command API can be added incrementally around existing operations without invalidating old project files.
- Qt equivalents should be used for browser-oriented performance requirements: paint only dirty regions, `QTimer` playhead updates, `QThread`/process workers, thumbnail/waveform caches, and visible-range timeline painting.

## Feature phases

### Phase 1 — Professional editor shell workflows (implemented)

- Original Lylis light visual style preserved at the user's request
- Resizable asset/preview/inspector/timeline splitters
- Collapsible asset library and inspector
- Preview focus mode with F11/Escape
- Fit/25/50/75/100 preview zoom
- 16:9, 9:16, 1:1, 4:5, and validated custom aspect ratios
- Saved/unsaved status
- Updated frame-navigation, redo, duplicate, and focus shortcuts
- Fixed the broken Add Layer route (`tab_container` → `tab_widget`)

### Phase 2 — Unified asset library

- Category rail for Media, Audio, Text, Lyrics, Stickers, Effects, Transitions, Filters, Adjustments, Captions, Templates, and Questions
- Shared search, recent/favorites, grid/list, rename/duplicate/delete actions
- Drag payloads from reusable assets to timeline adapters
- Lazy thumbnail and waveform cache

### Phase 3 — Preview transforms and inspector

- Resize/rotation handles, alignment/safe-area guides, center snapping
- Direct duplicate/hide/lock/reorder operations
- Visual inspector sections for transform, opacity, blend, crop/mask, border, shadow, and radius
- Text/lyric typography, karaoke colors, and animation sections

### Phase 4 — Non-destructive timeline commands

- Generic track adapters and track headers with lock/hide/mute/solo/reorder
- Clip copy/paste, ripple delete, grouping, multi-select, and transition handles
- Snap to clips/playhead/beats and visible-range painting
- Command-backed undo/redo for every timeline mutation

### Phase 5 — Karaoke, captions, animation, and audio

- Automatic word/syllable segmentation with draggable timing
- Active/current/next karaoke styling and animation presets
- Text In/Loop/Out animation duration and easing
- Audio normalize, EQ, enhancement, noise reduction, vocal/instrumental tools while preserving center vocal cut

### Phase 6 — Export and long-project performance

- Professional format/resolution/FPS/bitrate/audio/hardware options
- Progress, ETA, cancellation, and completion preview
- Proxy preview workflow, persistent waveform/thumbnail cache, and worker-based analysis/rendering
- Autosave recovery UI and migration-safe project versioning

## Compatibility rule

Every phase must load existing `.lylis.json` projects, preserve karaoke/media/template behavior, and pass the full regression suite before the next schema-affecting phase begins.
