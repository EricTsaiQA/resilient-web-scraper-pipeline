"""
Async Dual-Engine Fetcher (Static HTTP Fast Path + Playwright Dynamic Rendering Fallback).
Includes asyncio.Semaphore concurrency control, polite jitter, User-Agent rotation,
and exponential backoff retry.
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass
import random
import ssl
from typing import Awaitable, Callable, List, Optional
import urllib.request


USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
]


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay_sec: float = 0.05
    max_concurrency: int = 4
    jitter_max_sec: float = 0.02


class AsyncDualEngineFetcher:
    """
    Attempts fast static HTTP fetch first; if dynamic JS rendering is required or static fails,
    falls back to a pluggable async Playwright renderer.
    """

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        static_transport: Optional[Callable[[str, str], Awaitable[str]]] = None,
        playwright_fallback: Optional[Callable[[str], Awaitable[str]]] = None,
    ) -> None:
        self.cfg = config or RetryConfig()
        self._sem = asyncio.Semaphore(self.cfg.max_concurrency)
        self._static_transport = static_transport or self._default_urllib_fetch
        self._playwright_fallback = playwright_fallback

    @staticmethod
    async def _default_urllib_fetch(url: str, user_agent: str) -> str:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        def _sync_get() -> str:
            req = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                return resp.read().decode("utf-8", errors="ignore")

        return await asyncio.to_thread(_sync_get)

    async def fetch_html(self, url: str, require_js: bool = False) -> str:
        async with self._sem:
            last_error: Optional[Exception] = None
            for attempt in range(1, self.cfg.max_retries + 1):
                try:
                    if require_js and self._playwright_fallback is not None:
                        return await self._playwright_fallback(url)
                    ua = random.choice(USER_AGENTS)
                    html = await self._static_transport(url, ua)
                    if ("enable javascript" in html.lower() or len(html.strip()) < 40) and self._playwright_fallback:
                        return await self._playwright_fallback(url)
                    return html
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    if attempt < self.cfg.max_retries:
                        delay = self.cfg.base_delay_sec * (2 ** (attempt - 1)) + random.uniform(0, self.cfg.jitter_max_sec)
                        await asyncio.sleep(delay)

            if self._playwright_fallback is not None:
                return await self._playwright_fallback(url)
            raise RuntimeError(f"Failed to fetch {url} after {self.cfg.max_retries} attempts: {last_error}")
