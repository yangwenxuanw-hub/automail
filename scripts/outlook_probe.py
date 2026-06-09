from __future__ import annotations

import sys


def main() -> int:
    if not sys.platform.startswith("win"):
        print("This script requires Windows + Outlook desktop.")
        return 2

    import win32com.client  # type: ignore

    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")

    try:
        session = namespace.Session
        accounts = session.Accounts
        print("Accounts:")
        for idx in range(1, accounts.Count + 1):
            account = accounts.Item(idx)
            print(f"- {account.SmtpAddress}")
    except Exception:
        print("Accounts: unavailable")

    inbox = namespace.GetDefaultFolder(6)
    items = inbox.Items
    items.Sort("[ReceivedTime]", True)

    print("\nInbox (latest 10):")
    count = min(10, items.Count)
    for i in range(1, count + 1):
        mail = items.Item(i)
        subject = getattr(mail, "Subject", "")
        sender = getattr(mail, "SenderName", "")
        received = getattr(mail, "ReceivedTime", "")
        print(f"- {received} | {sender} | {subject}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
