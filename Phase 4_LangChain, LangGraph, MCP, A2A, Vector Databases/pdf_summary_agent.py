"""PDF summarization agent.

Features:
- Extracts text from a PDF file
- Summarizes the document with OpenAI when an API key is available
- Falls back to a local rule-based summary when no API key is configured
- CLI usage: python pdf_summary_agent.py my_file.pdf
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Optional

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - dependency setup help
    raise SystemExit(
        "Missing dependency: install it with `py -3 -m pip install pypdf`"
    ) from exc


class PDFSummaryAgent:
    """Summarize a PDF file using LLM support or a local fallback."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None, use_openai: Optional[bool] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.use_openai = bool(self.api_key) if use_openai is None else bool(use_openai and self.api_key)
        self.system_prompt = (
            "You are a careful research assistant. Summarize the PDF text in clear, concise language. "
            "Highlight the main idea, key findings, and important takeaways in a few bullet points."
        )

    def _clean_text(self, text: str) -> str:
        text = text.replace("\x00", "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def extract_text(self, pdf_path: str, max_pages: Optional[int] = None) -> str:
        """Read a PDF and extract all text content."""
        reader = PdfReader(pdf_path)
        pages = []
        total_pages = len(reader.pages)
        limit = total_pages if max_pages is None else min(max_pages, total_pages)
        print(f"Processing {limit} out of {total_pages} pages.")

        for page_number in range(limit):
            page = reader.pages[page_number]
            extracted = page.extract_text() or ""
            if extracted.strip():
                pages.append(extracted)

        extracted_text = "\n\n".join(pages)
        return self._clean_text(extracted_text)

    def _llm_summary(self, text: str) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Summarize this PDF content:\n\n{text[:15000]}"},
            ],
            "temperature": 0.2,
            "max_tokens": 500,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "echo": False,
            "expand": False,
        }

        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Language": "en-US",
                "model": self.model,
                "version": "v3",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                data["choices"][0]["message"]["content"] = self._clean_text(data["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed: {exc.code} {exc.reason}: {detail}") from exc

        return data["choices"][0]["message"]["content"].strip()

    def _fallback_summary(self, text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return "No readable text found in the PDF."

        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        meaningful = [s.strip() for s in sentences if s.strip()]
        if not meaningful:
            return "No summary could be generated from the PDF text."

        key_sentences = meaningful[: min(3, len(meaningful))]
        summary = " ".join(key_sentences)
        if len(summary) > 500:
            summary = summary[:500].rsplit(" ", 1)[0] + "..."
        return summary

    def summarize_pdf(self, pdf_path: str, max_pages: Optional[int] = None) -> str:
        """Extract text from a PDF and return a concise summary."""
        text = self.extract_text(pdf_path, max_pages=max_pages)
        if not text:
            raise ValueError("No readable text was found in the PDF.")

        if self.use_openai:
            try:
                return self._llm_summary(text)
            except Exception:
                return self._fallback_summary(text)

        return self._fallback_summary(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize the contents of a PDF file")
    parser.add_argument("pdf_path", help="Path to the PDF file to summarize")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to use when API access is available")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional limit on how many pages to read")
    parser.add_argument("--no-openai", action="store_true", help="Force the local fallback summary")
    parser.add_argument("--output", help="Optional path to write the summary to a text file")
    parser.add_argument("--echo", action="store_true", help="Print the summary to the console")
    args = parser.parse_args()
    args.model = "gpt-4o-mini"
    args.use_openai = True,
    args.echo = False,

    if not os.path.exists(args.pdf_path):
        parser.error(f"PDF file not found: {args.pdf_path}")
        parser.error(f"PDF file not found at path: {args.pdf_path}")

    agent = PDFSummaryAgent(model=args.model, use_openai=not args.no_openai)
    summary = agent.summarize_pdf(args.pdf_path, max_pages=args.max_pages)
    print(f"Summary for {args.pdf_path}:")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as out_file:
            out_file.write(summary)
        print(f"Summary saved to: {args.output}")
        print(f"Summary for {args.pdf_path}:")
        print(f"Summary for {args.pdf_path}:")

    if args.echo:
        print(summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
