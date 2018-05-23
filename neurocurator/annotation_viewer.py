#!/usr/bin/env python3.6

__author__ = "Pierre-Alexandre Fonta"
__maintainer__ = "Pierre-Alexandre Fonta"

import json
import re
import sys
from bisect import bisect, bisect_left
from functools import partial
from itertools import accumulate, chain, filterfalse
from math import ceil
from xml.dom import minidom

from PyQt5.QtCore import pyqtSlot, QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap, QTransform
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget, QFileDialog,
                             QLabel, QMenuBar, QScrollArea, QVBoxLayout, QWidget)
from fuzzysearch import find_near_matches
from popplerqt5 import Poppler


def debug(start_message, end_message):
    """Decorator printing messages before and after the function execution."""
    def debug_decorator(func):
        def func_wrapper(*args, **kwargs):
            print("\n{}...".format(start_message))
            func_return = func(*args, **kwargs)
            print("{}.".format(end_message))
            return func_return
        return func_wrapper
    return debug_decorator


class TextAnnotation:

    def __init__(self, category, text, shift_start=0, shift_end=0):
        self.category = category
        self.text = text  # Might be expanded with some context.
        self.shift_start = shift_start
        self.shift_end = shift_end
        self.boxes_span = None  # (start_index, end_index) in 'document_boxes'.
        self.highlightings = None  # dict(page_number -> rectangles)
        # TODO Use NeuroCurator's IDs. Currently: rank when sorted by 'boxes_span'.
        self.id = None

    def raw_text(self):
        """Return the annotation text without potential contextual expansion."""
        raw = self.text[self.shift_start:]
        if self.shift_end > 0:
            return raw[:-self.shift_end]
        else:
            return raw


class Mapper:

    def __init__(self, document, data_path):
        self.document = document

        self.annotations = []

        # DEBUG To visualize reordered blocks.
        # self.page_blocks = []

        # 'self' is required only for debugging.
        self.page_boxes = self._extract_boxes()

        # The indexes in 'document_boxes' of the first TextBox of each page.
        self.page_offsets = self._start_offsets(self.page_boxes)

        self.document_boxes = list(chain.from_iterable(self.page_boxes))

        document_words = [self._box_word(x) for x in self.document_boxes]

        self.document_text = "".join(document_words)

        # The starting offsets in 'document_text' of the text of each TextBox.
        self.word_offsets = self._start_offsets(document_words)

        self.load_annotations(data_path, False)
        self.locate_annotations()

    def load_annotations(self, path, is_omtd):
        """Load the annotations as TextAnnotation objects."""
        if path is not None:
            if is_omtd:
                self.annotations.extend(self._openminted_annotations(path, 10))
            else:
                self.annotations.extend(self._neurocurator_annotations(path))

    @debug("Locating annotations", "Annotations located")
    def locate_annotations(self):
        """Locate each loaded annotation. Build & Assign their highlighting."""
        for x in self.annotations:
            match = self._search(x)

            if match:
                x.boxes_span = match

                start_index, end_index = match

                start_page = bisect(self.page_offsets, start_index) - 1
                end_page = bisect(self.page_offsets, end_index) - 1

                if start_page == end_page:
                    boxes = self.document_boxes[start_index:end_index + 1]
                    x.highlightings = {start_page: list(self._build_chunks(boxes))}

                elif start_page == end_page - 1:
                    middle_index = self.page_offsets[end_page]
                    boxes_1 = self.document_boxes[start_index:middle_index]
                    boxes_2 = self.document_boxes[middle_index:end_index + 1]
                    rectangles_1 = list(self._build_chunks(boxes_1))
                    rectangles_2 = list(self._build_chunks(boxes_2))
                    x.highlightings = {start_page: rectangles_1, end_page: rectangles_2}

                else:
                    raise ValueError("Incorrect starting or ending page number!")

        # DEBUG.
        matched = [x for x in self.annotations if x.highlightings]
        sorted_ = sorted(matched, key=lambda x: x.boxes_span)
        for i, x in enumerate(sorted_):
            x.id = i
            print(x.id, list(x.highlightings.keys()), x.boxes_span, x.category,
                  repr(x.raw_text()), repr(x.text), sep="  #  ")
        total_count = len(self.annotations)
        matched_count = len(matched)
        not_matched_count = total_count - matched_count
        not_matched_rate = not_matched_count / total_count if total_count else 0
        print("TOTAL", total_count)
        print("MATCHED", matched_count)
        print("NOT MATCHED {} ({:.2f}%)".format(not_matched_count, not_matched_rate))

    @staticmethod
    def _openminted_annotations(xmi_path, context_length):
        """Return the annotations from OpenMinTeD as TextAnnotation objects."""
        xmi = minidom.parse(xmi_path)
        xmi_text = xmi.getElementsByTagName("cas:Sofa")[0].getAttribute("sofaString")
        xmi_text_length = len(xmi_text)

        for x in xmi.documentElement.childNodes:

            if x.tagName.startswith("neuro:"):
                start = int(x.getAttribute("begin"))
                end = int(x.getAttribute("end"))

                context_start = max(start - context_length, 0)
                context_end = min(end + context_length, xmi_text_length)

                text = xmi_text[context_start:context_end]

                shift_start = abs(context_start - start)
                shift_end = context_end - end

                yield TextAnnotation(x.localName, text, shift_start, shift_end)

    @staticmethod
    def _neurocurator_annotations(json_path):
        """Return the annotations from NeuroCurator as TextAnnotation objects."""
        with open(json_path, "r", encoding="utf-8") as f:
            annotations = (x["localizer"] for x in json.load(f))
            return (TextAnnotation("NeuroCurator", x["text"]) for x in annotations
                    if x["type"] == "text")

    @staticmethod
    def _clean(text):
        """Return the text cleaned of line breaks and unnecessary whitespaces."""
        # NB: str.split() removes repeated, leading, and trailing whitespaces.
        return " ".join(re.sub("[\u0000\U000c0000]", "", text).split())

    @staticmethod
    def _build_chunks(boxes):
        """Return the rectangles around chunks of TextBoxes which form a line."""
        chunk = QRectF()

        for x in boxes:
            chunk = chunk.united(x.boundingBox())
            if not x.nextWord():
                yield chunk
                chunk = QRectF()

        if not chunk.isNull():
            yield chunk

    @staticmethod
    def _start_offsets(sublists):
        """Return the offset in the concatenated sublists of each first element."""
        return list(accumulate([0] + [len(x) for x in sublists[:-1]]))

    @staticmethod
    def _box_word(box):
        """Return the text of a TextBox followed by a whitespace if relevant."""
        if box.hasSpaceAfter() or not box.nextWord():
            return box.text() + " "
        else:
            return box.text()

    def _search(self, annotation, max_dist=1):
        """Return the indexes in 'document_boxes' of the matched annotation text."""
        text = self._clean(annotation.text)

        near_matches = find_near_matches(text, self.document_text, max_l_dist=max_dist)

        if near_matches:
            # NB: min() returns the first minimal items encountered.
            closest_match = min(near_matches, key=lambda x: abs(x.dist))

            adjusted_start = closest_match.start + annotation.shift_start
            adjusted_end = closest_match.end - annotation.shift_end

            start_index = bisect(self.word_offsets, adjusted_start) - 1
            end_index = bisect_left(self.word_offsets, adjusted_end) - 1

            # DEBUG.
            ambiguities = len([x for x in near_matches
                               if abs(x.dist) == abs(closest_match.dist)])
            if ambiguities > 1:
                print("\tAMBIGUOUS", ambiguities, annotation.category,
                      repr(annotation.raw_text()), repr(text), sep="  #  ")

            return start_index, end_index

        elif max_dist > min(ceil(len(text) * 0.1), 20):
            # DEBUG.
            print("\tNOT MATCHED", max_dist, annotation.category,
                  repr(annotation.raw_text()), repr(text), sep="  #  ")

            return None

        else:
            return self._search(annotation, max_dist + 3)

    @debug("Parsing PDF", "PDF parsed")
    def _extract_boxes(self):
        """Return for each page its TextBoxes in a proper order."""
        num_pages = self.document.numPages()
        return [self._extract_page_boxes(i, 4, 4) for i in range(num_pages)]

    def _extract_page_boxes(self, page_number, ythreshold, xthreshold):
        """Return in a proper order the TextBoxes of a page."""
        page = self.document.page(page_number)

        page_size = page.pageSize()
        page_width = page_size.width()
        page_height = page_size.height()

        boxes = self.document.page(page_number).textList()

        # Utils.

        def is_vheader(chunk):
            rx = chunk.x()
            rw = chunk.width()
            rh = chunk.height()
            return min(rx, page_width - rx) < 30 and rw / rh < 0.1

        def detect_ysplits(chunks):
            slices = list(((ceil(x.top()), ceil(x.bottom())) for x in chunks))
            return detect_splits(slices, page_height, ythreshold)

        def detect_xsplits(chunks):
            slices = ((ceil(x.left()), ceil(x.right())) for x in chunks)
            return detect_splits(slices, page_width, xthreshold)

        def detect_splits(axis_slices, axis_dimension, axis_threshold):
            # Split when the space is greater than or equal to 2 * axis_threshold.
            pixels = [0] * (axis_dimension + 1)

            for start, end in axis_slices:
                s = start
                e = end + 1
                pixels[s:e] = [1] * (e - s)

                b = start - axis_threshold
                if 1 in pixels[b:s]:
                    pixels[b:s] = [1] * (s - b)

                a = end + axis_threshold + 1
                if 1 in pixels[e:a]:
                    pixels[e:a] = [1] * (a - e)

            p = None if pixels[0] == 1 else 0

            for i, x in enumerate(pixels[1:], start=1):
                if x == 1:
                    if p is not None:
                        yield (p, i - 1)
                        p = None
                else:
                    if p is None:
                        p = i

            if p is not None:
                yield (p, axis_dimension)

        def invert_slices(slices):
            return ((e1, s2) for (_, e1), (s2, _) in zip(slices[:-1], slices[1:]))

        def in_yblock(ystart, yend, chunk):
            return ceil(chunk.top()) >= ystart and ceil(chunk.bottom()) <= yend

        def detect_columns(yblocks_xsplits):
            p = yblocks_xsplits[0]

            if len(p[1]) < 3:
                yield p
                p = None

            for x in yblocks_xsplits[1:]:
                (ystart, yend), xsplits = x

                if len(xsplits) > 2:
                    # More than one column.
                    if p is None:
                        p = x
                    else:
                        (pystart, pyend), pxsplits = p
                        is_aligned = all_xsplits_aligned(pxsplits[1:-1], xsplits[1:-1])
                        is_same_section = ystart - pyend <= 15
                        if is_aligned and is_same_section:
                            # Merge.
                            p = (pystart, yend), list(merge_xsplits(pxsplits, xsplits))
                        else:
                            yield p
                            p = x
                else:
                    # Only one column.
                    if p is not None:
                        yield p
                        p = None
                    yield x

            if p is not None:
                yield p

        def all_xsplits_aligned(xsplits1, xsplits2):
            if len(xsplits1) != len(xsplits2):
                return False
            else:
                return all(are_xsplits_aligned(xs1, xs2)
                           for xs1, xs2 in zip(xsplits1, xsplits2))

        def are_xsplits_aligned(xsplit1, xsplit2):
            s1, e1 = xsplit1
            s2, e2 = xsplit2
            return abs(s1 - s2) <= xthreshold or abs(e1 - e2) <= xthreshold

        def merge_xsplits(xsplits1, xsplits2):
            for (start1, end1), (start2, end2) in zip(xsplits1, xsplits2):
                yield max(start1, start2), min(end1, end2)

        def build_blocks(yblocks_xblocks):
            for (ystart, yend), xsplits in yblocks_xblocks:
                for xstart, xend in xsplits:
                    yield QRectF(xstart, ystart, xend - xstart, yend - ystart)

        def reorder_chunks(chunks):
            return sorted(chunks, key=lambda r: (ceil(r.y()), ceil(r.x())))

        def in_chunk(chunk, box):
            return chunk.contains(box.boundingBox())

        # Group the bounding boxes as chunks (mainly: as lines).

        raw_chunks = self._build_chunks(boxes)

        # Exclude the bounding boxes part of vertical headers.

        chunks = list(filterfalse(is_vheader, raw_chunks))

        # Split horizontally the page.

        ysplits = detect_ysplits(chunks)

        # Deduce the horizontal blocks.

        yblocks = invert_slices(list(ysplits))

        # Split vertically each horizontal block.

        yblocks_chunks = (
            ((ystart, yend), filter(partial(in_yblock, ystart, yend), chunks))
            for (ystart, yend) in yblocks)

        yblocks_xsplits = [((ystart, yend), list(detect_xsplits(chunks)))
                           for (ystart, yend), chunks in yblocks_chunks]

        # Detect columns across continuous horizontal blocks.

        merged_yblocks_xsplits = detect_columns(yblocks_xsplits)

        # Deduce the vertical blocks.

        yblocks_xblocks = ((yslice, invert_slices(xsplits))
                           for yslice, xsplits in merged_yblocks_xsplits)

        # Build blocks.

        # By design blocks are ordered by increasing y and then increasing x.
        blocks = list(build_blocks(yblocks_xblocks))

        # DEBUG To visualize reordered blocks.
        # self.page_blocks.append(blocks)

        # Reorder the TextBoxes following the order of the blocks.

        # TODO Optimize by keeping the TextBoxes during the splitting?
        block_chunks = (filter(lambda y: x.contains(y), chunks) for x in blocks)
        reordered_chunks = chain.from_iterable(reorder_chunks(x) for x in block_chunks)
        reordered_boxes = (filter(partial(in_chunk, x), boxes) for x in reordered_chunks)

        return list(chain.from_iterable(reordered_boxes))


class DocumentView(QScrollArea):

    HIGHLIGHTING_COLORS = {
        "NeuroCurator": QColor(0, 0, 255, 70),  # Blue.
        "default": QColor(0, 255, 0, 70)  # Green.
    }

    INCH_TO_POINT = 72

    def __init__(self, pdf_path, data_path=None, parent=None):
        super().__init__(parent)

        # Variables section.

        self.scale_factor = 1

        self.document = Poppler.Document.load(pdf_path)
        self.document.setRenderHint(Poppler.Document.Antialiasing)
        self.document.setRenderHint(Poppler.Document.TextAntialiasing)

        self.num_pages = self.document.numPages()

        self.mapper = Mapper(self.document, data_path)

        # Own configuration section.

        display_size = QDesktopWidget().availableGeometry(self)

        self.resize(ceil(display_size.width() / 2), display_size.height())
        self.setAlignment(Qt.AlignHCenter)
        self.setWindowTitle("NeuroCurator - Annotation Viewer")

        # Widgets section.

        self.omtd_action = QAction("Load annotations from a XMI file")

        self.menu_bar = QMenuBar(self)

        self.omtd_menu = self.menu_bar.addMenu("OpenMinTeD")
        self.omtd_menu.addAction(self.omtd_action)

        self.render_document()

        # Signals section.

        self.omtd_action.triggered.connect(self.show_omtd_annotations)

    @pyqtSlot()
    def show_omtd_annotations(self):
        """Load & Locate OpenMinTeD annotations. Refresh the view to display them."""
        # TODO To be split in more specific slots.
        # TODO QFileDialog closes only when the method returns. Should be changed.
        path, _ = QFileDialog.getOpenFileName(self, "Open OpenMinTeD XMI", filter="*.xmi")

        if path:
            print("\nLoading OpenMinTeD annotations...")
            self.omtd_menu.setDisabled(True)
            self.mapper.load_annotations(path, True)
            self.mapper.locate_annotations()
            self.render_document()
            print("\nOpenMinTeD annotations loaded.")

    @debug("Rendering PDF", "PDF rendered")
    def render_document(self):
        """Render the document and its annotations."""
        layout = QVBoxLayout()
        for x in self._render_pages():
            layout.addWidget(x)
        widget = QWidget()
        widget.setLayout(layout)
        # NB: When a new widget is set, the current widget is destroyed.
        self.setWidget(widget)

    def _render_pages(self):
        """Return for each page its rendering as an image given a scale factor."""
        # NB: Both must be in dots per inch.
        xres = self.scale_factor * self.physicalDpiX()
        yres = self.scale_factor * self.physicalDpiY()

        transform = QTransform(xres / self.INCH_TO_POINT, 0, 0,
                               yres / self.INCH_TO_POINT, 0, 0)

        return (self._render_page(i, xres, yres, transform)
                for i in range(self.num_pages))

    def _render_page(self, page_number, xres, yres, transform):
        """Return the rendering as an image of a page and its annotations."""
        image = self.document.page(page_number).renderToImage(xres, yres)

        painter = QPainter()
        painter.begin(image)

        painter.setFont(QFont("Arial", 10))

        page_annotations = (x for x in self.mapper.annotations
                            if x.highlightings and page_number in x.highlightings)

        for x in page_annotations:
            # TODO Use more than one color for OpenMinTeD annotations.
            color = self.HIGHLIGHTING_COLORS.get(
                x.category, self.HIGHLIGHTING_COLORS["default"])
            # TODO Use a better way to indicate the type of an annotation.
            category_abbr = "".join(re.findall("[A-Z][a-z]", x.category))

            for y in x.highlightings[page_number]:
                rmapped = transform.mapRect(y)
                painter.fillRect(rmapped, color)
                painter.drawText(rmapped.adjusted(0, 8, 0, 8), Qt.AlignBottom |
                                 Qt.AlignLeft, "{} {}".format(x.id, category_abbr))

        # DEBUG Visualize reordered blocks.
        # See Mapper.__init__() and Mapper._extract_page_boxes().
        # from PyQt5.QtGui import QPen
        # blocks = self.mapper.page_blocks[page_number]
        # painter.setPen(QPen(QColor("red")))
        # for i, x in enumerate(blocks):
        #     rmapped = transform.mapRect(x)
        #     painter.drawRect(rmapped.adjusted(-4, -4, 4, 4))
        #     painter.drawText(rmapped.adjusted(-16, 0, 16, 0), Qt.AlignLeft, str(i))

        # DEBUG Visualize TextBoxes.
        # boxes = self.mapper.page_boxes[page_number]  # Reordered order.
        # # boxes = self.document.page(page_number).textList()  # Poppler order.
        # painter.setPen(QColor("red"))
        # painter.setFont(QFont("Arial", 10))
        # for i, x in enumerate(boxes):
        #     rmapped = transform.mapRect(x.boundingBox())
        #     color = QColor(0, 0, 255, 30) if x.nextWord() else QColor(255, 0, 0, 30)
        #     painter.fillRect(rmapped, color)
        #     painter.drawText(rmapped.adjusted(-5, 8, 5, 8), Qt.AlignBottom |
        #                      Qt.AlignCenter, str(i))

        painter.end()

        widget = QLabel()
        widget.setPixmap(QPixmap.fromImage(image))

        return widget


def main():
    app = QApplication(sys.argv)

    pdf_path = sys.argv[1]
    data_path = sys.argv[2] if len(sys.argv) == 3 else None

    view = DocumentView(pdf_path, data_path)
    view.show()

    # DEBUG.
    # print("\nDOCUMENT TEXT", view.mapper.document_text, sep="\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
