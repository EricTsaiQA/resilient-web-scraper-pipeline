"""
BYOK Webhook Notification Module for LINE Messaging API, Telegram Bot API, and Slack/Discord.
Sends concise diff alerts only when NEW or UPDATED records are detected.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from .diff_store import DiffRecord, DiffStatus


@dataclass
class WebhookAlertSummary:
    total_records: int
    new_count: int
    updated_count: int
    unchanged_count: int
    should_notify: bool
    message_text: str


def summarize_diff_for_alert(pipeline_name: str, diff_records: List[DiffRecord]) -> WebhookAlertSummary:
    new_items = [d for d in diff_records if d.status == DiffStatus.NEW]
    upd_items = [d for d in diff_records if d.status == DiffStatus.UPDATED]
    unchanged_count = len(diff_records) - len(new_items) - len(upd_items)
    should_notify = (len(new_items) + len(upd_items)) > 0

    lines = [
        f"🔔 [{pipeline_name}] Automated Data Pipeline Alert",
        f"• Total Scanned: {len(diff_records)}",
        f"• 🟢 NEW: {len(new_items)} | 🟡 UPDATED: {len(upd_items)} | ⚪ UNCHANGED: {unchanged_count}",
    ]
    for item in (new_items + upd_items)[:5]:
        r = item.record
        lines.append(f"  - [{item.status.value}] {r.region} {r.organization} ({r.phone} ext.{r.extension})")

    return WebhookAlertSummary(
        total_records=len(diff_records),
        new_count=len(new_items),
        updated_count=len(upd_items),
        unchanged_count=unchanged_count,
        should_notify=should_notify,
        message_text="\n".join(lines),
    )


def format_alert_message(pipeline_name: str, diff_records: List[DiffRecord]) -> str:
    return summarize_diff_for_alert(pipeline_name, diff_records).message_text


def send_webhook_alert(
    pipeline_name: str,
    diff_records: List[DiffRecord],
    channel: str = "line",
    sender: Optional[Callable[[str, Dict[str, object]], bool]] = None,
) -> WebhookAlertSummary:
    """
    Constructs channel-specific JSON payload (LINE Push / Telegram sendMessage / Slack webhook)
    and invokes the BYOK transport sender if NEW or UPDATED records exist.
    """
    summary = summarize_diff_for_alert(pipeline_name, diff_records)
    if not summary.should_notify or sender is None:
        return summary

    if channel == "line":
        payload: Dict[str, object] = {"messages": [{"type": "text", "text": summary.message_text}]}
    elif channel == "telegram":
        payload = {"text": summary.message_text, "parse_mode": "HTML"}
    else:
        payload = {"text": summary.message_text}

    sender(channel, payload)
    return summary
