"""Original file preview + PDF thumbnails."""

import pytest

from chronocare.services.preview import (
    ensure_thumbnail,
    is_pdf_path,
    preview_info,
    resolve_record_file,
)


def test_resolve_existing_png():
    path = resolve_record_file("uploads/medical_records/1_lab_report_p1.png")
    assert path is not None
    assert path.is_file()
    assert not is_pdf_path(path)


def test_resolve_existing_pdf():
    path = resolve_record_file("uploads/medical_records/11_血报告_qjh_250716.pdf")
    assert path is not None
    assert is_pdf_path(path)


def test_reject_path_traversal():
    assert resolve_record_file("../../etc/passwd") is None
    assert resolve_record_file("/etc/passwd") is None


def test_preview_info_pdf_and_missing():
    info = preview_info(11, "uploads/medical_records/11_血报告_qjh_250716.pdf")
    assert info.exists
    assert info.is_pdf
    assert info.preview_url == "/medical-records/11/preview"
    assert info.file_url == "/medical-records/11/file"

    missing = preview_info(9999, "uploads/medical_records/no-such-file.png")
    assert missing.exists is False
    assert missing.missing_path.endswith("no-such-file.png")


@pytest.mark.asyncio
async def test_pdf_thumbnail_generation(tmp_path, monkeypatch):
    import chronocare.services.preview as preview_mod

    monkeypatch.setattr(preview_mod, "THUMBNAIL_DIR", tmp_path)
    source = resolve_record_file("uploads/medical_records/11_血报告_qjh_250716.pdf")
    assert source is not None
    dest = await ensure_thumbnail(11, source)
    assert dest.is_file()
    assert dest.suffix == ".png"
    assert dest.stat().st_size > 1000


@pytest.mark.asyncio
async def test_http_preview_and_file(client, tmp_path, monkeypatch):
    import chronocare.services.preview as preview_mod

    monkeypatch.setattr(preview_mod, "THUMBNAIL_DIR", tmp_path)

    png = await client.get("/medical-records/1/preview")
    assert png.status_code == 200
    assert "image" in png.headers["content-type"]
    assert len(png.content) > 1000

    pdf_preview = await client.get("/medical-records/11/preview")
    assert pdf_preview.status_code == 200
    assert "image" in pdf_preview.headers["content-type"]
    assert pdf_preview.content[:8] == b"\x89PNG\r\n\x1a\n"

    original = await client.get("/medical-records/11/file")
    assert original.status_code == 200
    assert "pdf" in original.headers["content-type"]
    assert original.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_detail_page_does_not_use_pdf_as_img(client):
    html = (await client.get("/medical-records/11")).text
    assert 'src="/medical-records/11/preview"' in html
    assert "打开原件" in html
    assert 'src="/uploads/medical_records/11' not in html


@pytest.mark.asyncio
async def test_list_shows_recognized(client):
    html = (await client.get("/medical-records", params={"record_type": "lab_report"})).text
    assert "已识别" in html
    assert html.count("待识别") == 0


@pytest.mark.asyncio
async def test_png_detail_preview(client):
    html = (await client.get("/medical-records/1")).text
    assert 'src="/medical-records/1/preview"' in html
    assert "原件预览" in html
