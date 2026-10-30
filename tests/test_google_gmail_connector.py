from pathlib import Path

from life_os.connectors.google_gmail import (
    GMAIL_READ_SCOPE,
    list_gmail_accounts,
    register_gmail_account,
    safe_account_id,
)


def test_registers_multiple_household_accounts_without_tokens_in_registry(
    tmp_path: Path,
) -> None:
    registry = tmp_path / "gmail-accounts.json"
    register_gmail_account(
        registry,
        account_id="alex",
        email="alex@example.com",
        member_name="Alex",
        token_path=tmp_path / "alex-token.json",
    )
    register_gmail_account(
        registry,
        account_id="sam",
        email="sam@example.com",
        member_name="Sam",
        token_path=tmp_path / "sam-token.json",
    )

    accounts = list_gmail_accounts(registry)
    assert [account["member_name"] for account in accounts] == ["Alex", "Sam"]
    assert accounts[1]["scopes"] == [GMAIL_READ_SCOPE]
    assert "token_file" not in accounts[1]
    assert registry.stat().st_mode & 0o777 == 0o600


def test_account_id_is_safe_for_private_token_filename() -> None:
    assert safe_account_id("Sam Family") == "sam-family"
