FORM = {"title": "Upload test", "meeting_date": "2026-11-23"}


def upload(client, name, content):
    return client.post("/api/meetings/upload", data=FORM, files={"file": (name, content, "text/plain")})


def test_accepts_txt_vtt_and_md(alice):
    for name in ["notes.txt", "captions.vtt", "notes.md"]:
        response = upload(alice, name, b"Ann: hello there.")
        assert response.status_code == 201, response.text


def test_stores_the_transcript_text(alice):
    response = upload(alice, "notes.txt", "Ann: hello.".encode("utf-8-sig"))
    meeting = alice.get(f"/api/meetings/{response.json()['id']}").json()
    assert meeting["transcript"] == "Ann: hello."


def test_rejects_unsupported_file_type(alice):
    assert upload(alice, "notes.pdf", b"%PDF-1.4").status_code == 415


def test_rejects_empty_file(alice):
    assert upload(alice, "notes.txt", b"   \n").status_code == 422


def test_rejects_file_over_the_size_limit(alice):
    assert upload(alice, "big.txt", b"a" * 200_001).status_code == 413
