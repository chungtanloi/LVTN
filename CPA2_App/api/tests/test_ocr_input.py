import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pypdfium2 as pdfium
from PIL import Image
from fastapi.testclient import TestClient

from cpa2_api.main import app
from cpa2_api.ocr_input import OcrInputError, read_pages


def pdf_bytes(count=1, width=612, height=792):
    with pdfium.PdfDocument.new() as doc:
        for _ in range(count):
            doc.new_page(width, height).close()
        output = io.BytesIO()
        doc.save(output)
        return output.getvalue()


class PdfInputTests(unittest.TestCase):
    def test_renders_four_pages_as_detached_images(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.pdf'
            path.write_bytes(pdf_bytes(4))
            images = read_pages([path])
        try:
            self.assertEqual(len(images), 4)
            for image in images:
                self.assertEqual(image.width, 2448)
                self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))
        finally:
            for image in images:
                image.close()

    def test_rejects_invalid_pdf_excess_pages_and_extreme_geometry(self):
        for data in (b'%PDF-broken', pdf_bytes(5), pdf_bytes(1, 1, 10000)):
            with self.subTest(size=len(data)), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'test.pdf'
                path.write_bytes(data)
                with self.assertRaises(OcrInputError):
                    read_pages([path])

    def test_page_limit_counts_pdf_and_images_together(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / 'test.pdf'
            pdf.write_bytes(pdf_bytes(4))
            png = Path(directory) / 'page.png'
            Image.new('RGB', (20, 20), 'white').save(png)
            for paths in ([pdf, png], [png, pdf]):
                with self.assertRaises(OcrInputError):
                    read_pages(paths)

    def test_http_uses_pdf_signature_instead_of_filename(self):
        import os
        with patch.dict(os.environ, {'CPA2_SERVICE_KEY': 'pdf-test-key'}):
            async def inspect(operation, payload, timeout):
                self.assertEqual(operation, 'ocr')
                self.assertEqual(Path(payload['paths'][0]).suffix, '.pdf')
                return {'needs_review': True}
            with patch('cpa2_api.main.run', new=inspect):
                response = TestClient(app).post('/v1/ocr',
                    files={'files': ('wrong.png', pdf_bytes(), 'image/png')},
                    headers={'Authorization': 'Bearer pdf-test-key'})
        self.assertEqual(response.status_code, 200)

    def test_http_invalid_pdf_is_a_user_error(self):
        import os
        with patch.dict(os.environ, {'CPA2_SERVICE_KEY': 'pdf-test-key'}):
            response = TestClient(app).post('/v1/ocr',
                files={'files': ('broken.pdf', b'%PDF-broken', 'application/pdf')},
                headers={'Authorization': 'Bearer pdf-test-key'})
        self.assertEqual(response.status_code, 422, response.text)
