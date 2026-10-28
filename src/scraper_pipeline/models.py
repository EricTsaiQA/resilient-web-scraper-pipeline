"""
Data Cleaning & Schema Validation Module.
Handles full-width to half-width Unicode normalization (NFKC), whitespace collapsing,
and phone/extension splitting for Taiwan & international directory records.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import re
import unicodedata
from typing import Dict, Tuple


def normalize_fullwidth_text(raw: str) -> str:
    """Converts full-width characters (e.g., （０３）５２１－６１２１) to standard half-width ASCII."""
    if not raw:
        return ""
    norm = unicodedata.normalize("NFKC", raw)
    return re.sub(r"\s+", " ", norm).strip()


def parse_and_normalize_phone(raw_phone: str, raw_ext: str = "") -> Tuple[str, str]:
    """
    Standardizes phone numbers like '03-5216121#302' or '（０４）２２２８－９１１１ 分機 1234'
    into clean `(03)521-6121` and extension `302`.
    """
    cleaned = normalize_fullwidth_text(raw_phone)
    ext_clean = normalize_fullwidth_text(raw_ext).lstrip("#").strip()

    ext_match = re.search(r"(?:#|分機|轉|ext\.?)\s*([0-9、~～\-~,，\s]+)$", cleaned, flags=re.IGNORECASE)
    if ext_match:
        extracted_ext = ext_match.group(1).strip()
        if not ext_clean:
            ext_clean = extracted_ext
        cleaned = cleaned[: ext_match.start()].strip()

    digits_match = re.match(r"^\(?0(\d{1,2})\)?[-\s]*(\d{3,4})[-\s]*(\d{4})$", cleaned)
    if digits_match:
        area, p1, p2 = digits_match.groups()
        cleaned = f"(0{area}){p1}-{p2}"

    return cleaned, ext_clean


@dataclass
class DirectoryContactRecord:
    record_id: str
    region: str
    organization: str
    department_or_duty: str
    phone: str
    extension: str
    fax: str
    address: str
    email_or_url: str
    source_url: str
    scraped_at: str

    @classmethod
    def from_raw(
        cls,
        record_id: str,
        region: str,
        organization: str,
        department_or_duty: str,
        phone: str,
        extension: str = "",
        fax: str = "",
        address: str = "",
        email_or_url: str = "",
        source_url: str = "",
        scraped_at: str = "",
    ) -> "DirectoryContactRecord":
        norm_phone, norm_ext = parse_and_normalize_phone(phone, extension)
        norm_fax, _ = parse_and_normalize_phone(fax)
        org_clean = normalize_fullwidth_text(organization)
        if not org_clean:
            raise ValueError("organization cannot be empty")

        return cls(
            record_id=normalize_fullwidth_text(record_id),
            region=normalize_fullwidth_text(region),
            organization=org_clean,
            department_or_duty=normalize_fullwidth_text(department_or_duty),
            phone=norm_phone,
            extension=norm_ext or "N/A",
            fax=norm_fax or "N/A",
            address=normalize_fullwidth_text(address),
            email_or_url=normalize_fullwidth_text(email_or_url),
            source_url=normalize_fullwidth_text(source_url),
            scraped_at=normalize_fullwidth_text(scraped_at),
        )

    def content_fingerprint(self) -> str:
        """Deterministic SHA-256 fingerprint of business fields (excluding scraped_at timestamp)."""
        payload = "|".join(
            [
                self.record_id,
                self.region,
                self.organization,
                self.department_or_duty,
                self.phone,
                self.extension,
                self.fax,
                self.address,
                self.email_or_url,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)
