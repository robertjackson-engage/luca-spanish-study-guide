# Crush Quest — Luca's Spanish Quest

Spanish 1 study platform for Luca — Lección 2.1 & 2.3 (present tense of -ar verbs, gustar, estar, and where things are). Open `index.html` or visit the Pages URL.

Story: Valentina, an exchange student from Madrid, only speaks Spanish and the dance is Friday. Correct Spanish fills her heart meter; pass the Boss Test at 90% to ask her. Her lines and Luca's are voiced with their own ElevenLabs voices (`audio/v-*.mp3`, `audio/l-*.mp3`).

Five game zones map one-to-one to the five sections of the test, in the same format, plus a Boss Test that generates a fresh 23-point mock exam. Every Spanish phrase is voiced and every action has a sound effect.

## Updating

Edit `index.html`, then:

```bash
git commit -am "update" && git push
```

## Audio

Voice clips and sound effects in `audio/` were pre-generated with ElevenLabs by `tools/gen_audio.py`, so the published site is fully static and contains no API key. To regenerate (only new phrases are generated; existing files are skipped):

1. Put `ELEVENLABS_API_KEY=...` in a local `.env` file (it is gitignored).
2. In the browser console on `index.html`, run `copy(JSON.stringify(AUDIO_TEXTS()))` (narrator) or `copy(JSON.stringify(AUDIO_TEXTS_BY_VOICE()))` (character lines) and save that to `texts.json`.
3. Run:

```bash
set -a && source .env && set +a && python3 tools/gen_audio.py texts.json
```
