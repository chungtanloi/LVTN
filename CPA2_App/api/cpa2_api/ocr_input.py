"""Bounded PDF rendering inside the time-limited OCR worker process."""
import math
from pathlib import Path

from PIL import Image
import pypdfium2 as pdfium


class OcrInputError(ValueError):
    pass


def read_pages(paths):
    images = []
    try:
        for path in paths:
            if Path(path).suffix.lower() != '.pdf':
                with Image.open(path) as source:
                    images.append(source.convert('RGB'))
            else:
                try:
                    with pdfium.PdfDocument(path) as document:
                        if not 1 <= len(document) <= 4 - len(images):
                            raise OcrInputError()
                        for page in document:
                            try:
                                width, height = page.get_size()
                                if not all(math.isfinite(x) and 0 < x < 14400 for x in (width, height)):
                                    raise OcrInputError()
                                scale = 2448 / width
                                if math.ceil(width * scale) * math.ceil(height * scale) > 20_000_000:
                                    raise OcrInputError()
                                bitmap = page.render(scale=scale)
                                try:
                                    images.append(bitmap.to_pil().convert('RGB'))
                                finally:
                                    bitmap.close()
                            finally:
                                page.close()
                except (pdfium.PdfiumError, ValueError, OverflowError):
                    raise OcrInputError() from None
            if len(images) > 4:
                raise OcrInputError()
        return images
    except BaseException:
        for image in images:
            image.close()
        raise
