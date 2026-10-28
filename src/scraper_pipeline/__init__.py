"""
resilient-web-scraper-pipeline
Production-grade Python Scraping, Data Normalization, Hash Diff Tracking,
Styled Excel/CSV Export, and LINE/Telegram Webhook Notification Pipeline.
Author: Eric Tsai (EricTsaiQA) — e3t4fun Studio
"""
from .models import DirectoryContactRecord, normalize_fullwidth_text, parse_and_normalize_phone
from .engine import AsyncDualEngineFetcher, RetryConfig
from .diff_store import DiffRecord, DiffSnapshotStore, DiffStatus
from .exporters import export_diff_to_csv, export_diff_to_excel
from .notifiers import WebhookAlertSummary, format_alert_message, send_webhook_alert

__all__ = [
    "DirectoryContactRecord",
    "normalize_fullwidth_text",
    "parse_and_normalize_phone",
    "AsyncDualEngineFetcher",
    "RetryConfig",
    "DiffRecord",
    "DiffSnapshotStore",
    "DiffStatus",
    "export_diff_to_csv",
    "export_diff_to_excel",
    "WebhookAlertSummary",
    "format_alert_message",
    "send_webhook_alert",
]
