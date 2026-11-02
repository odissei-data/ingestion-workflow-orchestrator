from tasks.base_tasks import sanitize_emails


def test_email_addresses_are_removed():
    xml = b'<contact>Mail test.something@dans.knaw.nl or info@cbs.nl.</contact>'
    assert sanitize_emails.fn(xml) == b'<contact>Mail  or .</contact>'


def test_replacement_email():
    xml = b'Check that test.something@dans.knaw.nl is sanitized.'
    assert sanitize_emails.fn(xml, 'test@example.com') == \
        b'Check that test@example.com is sanitized.'


def test_text_without_email_is_unchanged():
    xml = '<title>Inkomen @ huishoudens, één tabel</title>'.encode('utf-8')
    assert sanitize_emails.fn(xml) == xml
