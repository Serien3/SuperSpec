#!/usr/bin/env python3
"""Send one email via SMTP.

Examples:
  python3 script/send_email_smtp.py \\
    --email your_account@outlook.com \\
    --password 'your_app_password' \\
    --to to@example.com --subject "Hello" --body "This is a test"
"""

from __future__ import annotations

import argparse
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send an email via SMTP")
    parser.add_argument(
        "--to",
        action="append",
        required=True,
        help="Recipient email. Repeat this flag for multiple recipients.",
    )
    parser.add_argument("--subject", required=True, help="Email subject")

    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body", help="Plain text email body")
    body_group.add_argument("--body-file", help="Read plain text body from file")

    parser.add_argument(
        "--host",
        default="smtp.office365.com",
        help="SMTP host (default: smtp.office365.com)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=587,
        help="SMTP port (default: 587)",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="SMTP login email and From address",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="SMTP password/app password",
    )
    parser.add_argument(
        "--ssl",
        action="store_true",
        help="Use SMTP over SSL (usually port 465)",
    )
    parser.add_argument(
        "--no-starttls",
        action="store_true",
        help="Disable STARTTLS for plain SMTP connection",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Connection timeout in seconds (default: 20)",
    )

    return parser.parse_args()


def normalize_recipients(raw_recipients: list[str]) -> list[str]:
    recipients: list[str] = []
    for item in raw_recipients:
        parts = [part.strip() for part in item.split(",") if part.strip()]
        recipients.extend(parts)
    return recipients


def read_body(args: argparse.Namespace) -> str:
    if args.body is not None:
        return args.body
    return Path(args.body_file).read_text(encoding="utf-8")


def validate_required(args: argparse.Namespace) -> None:
    missing: list[str] = []
    if not args.host:
        missing.append("SMTP host (--host)")
    if missing:
        raise ValueError("Missing required config: " + "; ".join(missing))


def build_message(from_addr: str, recipients: list[str], subject: str, body: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = from_addr
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)
    return message


def send_mail(args: argparse.Namespace) -> None:
    recipients = normalize_recipients(args.to)
    if not recipients:
        raise ValueError("At least one valid recipient is required")

    validate_required(args)
    body = read_body(args)
    message = build_message(args.email, recipients, args.subject, body)

    context = ssl.create_default_context()

    if args.ssl:
        with smtplib.SMTP_SSL(args.host, args.port, timeout=args.timeout, context=context) as server:
            server.login(args.email, args.password)
            server.send_message(message)
        return

    with smtplib.SMTP(args.host, args.port, timeout=args.timeout) as server:
        server.ehlo()
        if not args.no_starttls:
            server.starttls(context=context)
            server.ehlo()
        server.login(args.email, args.password)
        server.send_message(message)


def main() -> int:
    args = parse_args()
    try:
        send_mail(args)
    except Exception as exc:  # pragma: no cover - CLI entrypoint safety
        print(f"Failed to send email: {exc}", file=sys.stderr)
        return 1

    recipients = ", ".join(normalize_recipients(args.to))
    print(f"Email sent successfully to: {recipients}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
