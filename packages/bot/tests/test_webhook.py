from src.automa.bot.webhook import generate_webhook_signature, verify_webhook


def test_returns_false_if_secret_is_not_a_string():
    result = verify_webhook(1, "signature", "{}")

    assert result is False


def test_returns_false_if_secret_is_empty():
    result = verify_webhook("", "signature", "{}")

    assert result is False


def test_returns_false_if_signature_is_not_a_string():
    result = verify_webhook("secret", 1, "{}")

    assert result is False


def test_returns_false_if_signature_is_empty():
    result = verify_webhook("secret", "", "{}")

    assert result is False


def test_throws_error_if_secret_does_not_start_with_atma_whsec():
    try:
        verify_webhook("invalid_secret", "signature", "{}")
    except ValueError as e:
        assert str(e) == "Secret must start with 'atma_whsec_'"


def test_throws_error_if_payload_is_not_a_valid_json():
    try:
        verify_webhook("atma_whsec_secret", "signature", "not a json")
    except ValueError as e:
        assert str(e) == "Invalid payload format"


def test_throws_error_if_payload_is_not_a_dict():
    try:
        verify_webhook("atma_whsec_secret", "signature", '["not", "a", "dict"]')
    except ValueError as e:
        assert str(e) == "Invalid payload format"


def test_throws_error_if_payload_does_not_contain_id():
    try:
        verify_webhook(
            "atma_whsec_secret", "signature", '{"timestamp": "2023-10-01T00:00:00Z"}'
        )
    except ValueError as e:
        assert str(e) == "Payload must contain both 'id' and 'timestamp' fields"


def test_throws_error_if_payload_does_not_contain_timestamp():
    try:
        verify_webhook("atma_whsec_secret", "signature", '{"id": "1"}')
    except ValueError as e:
        assert str(e) == "Payload must contain both 'id' and 'timestamp' fields"


def test_returns_false_if_signature_is_wrong():
    result = verify_webhook(
        "atma_whsec_secret",
        "signature",
        '{"id": "1", "timestamp": "2023-10-01T00:00:00Z"}',
    )

    assert result is False


def test_returns_true_if_signature_is_correct():
    result = verify_webhook(
        "atma_whsec_secret",
        "v1,/VB+gt7CALYoWLO0Pym4MfxP3l4a29h1OYQcfJ59D+E=",
        '{"id": "1", "timestamp": "2023-10-01T00:00:00Z"}',
    )

    assert result is True


def test_returns_true_if_second_signature_is_correct():
    result = verify_webhook(
        "atma_whsec_secret",
        "bad_signature v1,/VB+gt7CALYoWLO0Pym4MfxP3l4a29h1OYQcfJ59D+E=",
        '{"id": "1", "timestamp": "2023-10-01T00:00:00Z"}',
    )

    assert result is True


def test_verifies_the_generated_signature():
    # Generate signature
    signature = generate_webhook_signature(
        "atma_whsec_secret", '{"id": "1", "timestamp": "2023-10-01T00:00:00Z"}'
    )

    # Verify with the same parameters
    result = verify_webhook(
        "atma_whsec_secret",
        signature,
        '{"id": "1", "timestamp": "2023-10-01T00:00:00Z"}',
    )

    assert result is True
