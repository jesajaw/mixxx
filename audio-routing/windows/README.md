# System audio -> Mixxx on Windows

Mixxx has no built-in "loopback" input. You need a virtual audio cable.

1. Install **VB-CABLE** (donationware, vb-audio.com) or **VoiceMeeter** and reboot.
2. Route the Spotify app or your browser to the cable:
   *Windows Settings > System > Sound > Volume mixer* (or "App volume and device preferences")
   -> set the app's **output = CABLE Input**.
3. In Mixxx: *Preferences > Sound Hardware > Input*:
   **Auxiliary 1 = CABLE Output**, channels 1-2. Keep the outputs (master/headphones) on
   your real device (ideally ASIO, or WASAPI with a small buffer size).
4. In Mixxx: show the Aux section in the skin (StudioDeck shows the Mic/Aux rack by default),
   raise the Aux fader, and use PFL for headphone cueing if needed.

Notes
* The Spotify app is then only audible through the Mixxx mixer (no longer directly on your speakers).
* Do not route Windows system sounds to the cable, or they end up in the mix.
* Leave the Spotify volume at about 100 % and control the level in Mixxx with Aux gain/fader.
