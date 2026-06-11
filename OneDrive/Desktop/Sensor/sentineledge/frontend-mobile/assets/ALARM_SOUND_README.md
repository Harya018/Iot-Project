# Assets Required

## alarm.mp3
Place an alarm sound file at:
  frontend-mobile/assets/alarm.mp3

This file is used by `src/components/AlertOverlay.js` to play a looping alarm when an alert fires.

### Recommended sources:
- Use any short (2-5s) looping alarm sound in MP3 format
- Free sources: freesound.org, mixkit.co (royalty-free)
- Filename must be exactly: alarm.mp3
- Place it directly in the `assets/` folder

The app will still function without this file — the AlertOverlay handles the missing file gracefully
with a console warning, and the haptic vibration will still work.
