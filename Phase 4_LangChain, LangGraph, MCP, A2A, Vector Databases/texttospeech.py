"""Basic text-to-speech demo."""

from __future__ import annotations

import argparse


def speak_text(text: str, rate: int = 180) -> None:
    """Speak text using pyttsx3."""
    try:
        import pyttsx3
    except ImportError as exc:
        raise SystemExit(
            "pyttsx3 is not installed. Install it with: pip install pyttsx3"
        ) from exc

    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.say(text)
    engine.runAndWait()
    engine.close()



def main() -> None:
    parser = argparse.ArgumentParser(description="Basic text-to-speech example")
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to speak. If omitted, the program will ask for input.",
        use_unicode=True,
        blank=True,
        show_default=True,
        required=False,
        type=str,
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=180,
        help="Speaking rate (default: 180)",
        show_default=True,
        envvar="SpeakingRate",
        dest="rate",
        width=10,
        required=False,
    )
    args = parser.parse_args()

    text = args.text if args.text else input("Enter text to speak: ").strip()
    if not text:
        raise SystemExit("No text provided.")
    else:
        speak_text(text, rate=args.rate)



    print(f"Speaking: {text}")




if __name__ == "__main__":
    main()
