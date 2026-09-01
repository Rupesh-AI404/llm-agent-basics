"""Background removal agent for image files.

This agent removes image backgrounds and saves the result as a transparent PNG.
It uses `rembg` for the segmentation step and Pillow for file handling.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - dependency setup help
    raise SystemExit("Missing dependency: install Pillow with `py -3 -m pip install pillow`") from exc

try:
    from rembg import remove
except ImportError as exc:  # pragma: no cover - dependency setup help
    raise SystemExit("Missing dependency: install rembg with `py -3 -m pip install rembg`") from exc


class BackgroundRemovalAgent:
    """Remove image backgrounds and persist the transparent result."""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir).expanduser().resolve() if output_dir else None

    def _resolve_output_path(self, input_path: Path, output_path: Optional[str]) -> Path:
        if output_path:
            resolved = Path(output_path).expanduser().resolve()
            if resolved.suffix.lower() != ".png":
                resolved = resolved.with_suffix(".png")
            return resolved

        target_dir = self.output_dir or input_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / f"{input_path.stem}_no_bg.png"

    def remove_background(self, input_path: str, output_path: Optional[str] = None) -> Path:
        """Remove the background from one image and return the saved path."""
        source = Path(input_path).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Image not found: {source}")
        if not source.is_file():
            raise ValueError(f"Input path is not a file: {source}")

        target = self._resolve_output_path(source, output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        image_bytes = source.read_bytes()
        result_bytes = remove(image_bytes)
        with Image.open(io.BytesIO(result_bytes)) as result_image:
            result_image = result_image.convert("RGBA")
            result_image.save(target, format="PNG")
            result_image.close()

        return target

    def remove_background_batch(self, input_dir: str, output_dir: Optional[str] = None) -> list[Path]:
        """Remove backgrounds from every image in a directory."""
        source_dir = Path(input_dir).expanduser().resolve()
        if not source_dir.exists():
            raise FileNotFoundError(f"Directory not found: {source_dir}")
        if not source_dir.is_dir():
            raise ValueError(f"Input path is not a directory: {source_dir}")

        target_dir = Path(output_dir).expanduser().resolve() if output_dir else source_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        results: list[Path] = []
        for image_path in sorted(source_dir.iterdir()):
            if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
                continue
            saved_path = self.remove_background(str(image_path), str(target_dir / f"{image_path.stem}_no_bg.png"))
            results.append(saved_path)

        return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Remove the background from an image")
    parser.add_argument("input", help="Path to an image file or a directory of images")
    parser.add_argument("-o", "--output", help="Output PNG path for a single image")
    parser.add_argument("--output-dir", help="Directory for batch output or the default single-image output")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    agent = BackgroundRemovalAgent(output_dir=args.output_dir)
    source = Path(args.input)

    if source.is_dir():
        results = agent.remove_background_batch(args.input, output_dir=args.output_dir)
        for item in results:
            print(item)
        return 0

    saved_path = agent.remove_background(args.input, args.output)
    print(saved_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
