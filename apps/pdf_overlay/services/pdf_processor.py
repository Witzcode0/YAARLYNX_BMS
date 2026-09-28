from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

import io


# ============================================================
# SETTINGS
# ============================================================

ORIGINAL_WIDTH = 150
ORIGINAL_HEIGHT = 60

# 3X image size
IMAGE_WIDTH = ORIGINAL_WIDTH * 3
IMAGE_HEIGHT = ORIGINAL_HEIGHT * 3

# Distance from bottom of PDF page
BOTTOM_MARGIN = 0


# ============================================================
# POSITION CALCULATION
# ============================================================

def calculate_position(
    page_width,
    page_height,
    position
):
    """
    Calculate image X/Y position on PDF page.
    """

    # -----------------------------------------
    # Bottom Left
    # -----------------------------------------

    if position == "bottom_left":

        x = 0
        y = BOTTOM_MARGIN


    # -----------------------------------------
    # Bottom Center
    # -----------------------------------------

    elif position == "bottom_center":

        x = (
            page_width - IMAGE_WIDTH
        ) / 2

        y = BOTTOM_MARGIN


    # -----------------------------------------
    # Bottom Right
    # -----------------------------------------

    elif position == "bottom_right":

        x = (
            page_width
            - IMAGE_WIDTH
        )

        y = BOTTOM_MARGIN


    # -----------------------------------------
    # Top Left
    # -----------------------------------------

    elif position == "top_left":

        x = 0

        y = (
            page_height
            - IMAGE_HEIGHT
        )


    # -----------------------------------------
    # Top Center
    # -----------------------------------------

    elif position == "top_center":

        x = (
            page_width - IMAGE_WIDTH
        ) / 2

        y = (
            page_height
            - IMAGE_HEIGHT
        )


    # -----------------------------------------
    # Top Right
    # -----------------------------------------

    elif position == "top_right":

        x = (
            page_width
            - IMAGE_WIDTH
        )

        y = (
            page_height
            - IMAGE_HEIGHT
        )


    # -----------------------------------------
    # Center
    # -----------------------------------------

    elif position == "center":

        x = (
            page_width - IMAGE_WIDTH
        ) / 2

        y = (
            page_height - IMAGE_HEIGHT
        ) / 2


    # -----------------------------------------
    # Default
    # -----------------------------------------

    else:

        x = (
            page_width - IMAGE_WIDTH
        ) / 2

        y = BOTTOM_MARGIN


    return x, y


# ============================================================
# APPLY OVERLAY
# ============================================================

def apply_overlay(
    pdf_file,
    image_path,
    position="bottom_center"
):
    """
    Add overlay image to every page of PDF.

    Parameters
    ----------
    pdf_file:
        Uploaded Django PDF file.

    image_path:
        Path of saved overlay image.

    position:
        Position of overlay.

    Returns
    -------
    BytesIO
        Processed PDF in memory.
    """

    # ========================================================
    # READ INPUT PDF
    # ========================================================

    reader = PdfReader(
        pdf_file
    )

    writer = PdfWriter()


    # ========================================================
    # PROCESS EVERY PAGE
    # ========================================================

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        # ---------------------------------------------
        # Get PDF page dimensions
        # ---------------------------------------------

        page_width = float(
            page.mediabox.width
        )

        page_height = float(
            page.mediabox.height
        )


        # ---------------------------------------------
        # Create temporary PDF overlay
        # ---------------------------------------------

        packet = io.BytesIO()


        c = canvas.Canvas(
            packet,
            pagesize=(
                page_width,
                page_height
            )
        )


        # ---------------------------------------------
        # Calculate image position
        # ---------------------------------------------

        x, y = calculate_position(
            page_width=page_width,
            page_height=page_height,
            position=position
        )


        # ---------------------------------------------
        # Draw image
        # ---------------------------------------------

        c.drawImage(
            ImageReader(image_path),
            x,
            y,
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            preserveAspectRatio=True,
            mask="auto"
        )


        # ---------------------------------------------
        # Save temporary overlay PDF
        # ---------------------------------------------

        c.save()


        # ---------------------------------------------
        # Read overlay PDF
        # ---------------------------------------------

        packet.seek(0)

        overlay_reader = PdfReader(
            packet
        )

        overlay_page = (
            overlay_reader.pages[0]
        )


        # ---------------------------------------------
        # Merge overlay with original page
        # ---------------------------------------------

        page.merge_page(
            overlay_page
        )


        # ---------------------------------------------
        # Add modified page
        # ---------------------------------------------

        writer.add_page(
            page
        )


    # ========================================================
    # CREATE FINAL PDF IN MEMORY
    # ========================================================

    output = io.BytesIO()

    writer.write(
        output
    )

    output.seek(0)

    return output