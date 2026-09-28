from django.shortcuts import render
from django.http import FileResponse

from .models import OverlayImage
from .services.pdf_processor import apply_overlay


def pdf_overlay_view(request):

    # ========================================================
    # GET ALL OVERLAY IMAGES
    # ========================================================

    overlay_images = OverlayImage.objects.all()


    # ========================================================
    # GET DEFAULT OVERLAY
    # ========================================================

    default_overlay = OverlayImage.objects.filter(
        is_default=True
    ).first()


    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        # ----------------------------------------------------
        # GET UPLOADED PDF
        # ----------------------------------------------------

        pdf_file = request.FILES.get(
            "pdf_file"
        )


        # ----------------------------------------------------
        # Validate PDF
        # ----------------------------------------------------

        if not pdf_file:

            return render(
                request,
                "pdf_overlay/overlay.html",
                {
                    "overlay_images": overlay_images,
                    "default_overlay": default_overlay,
                    "error": "Please upload a PDF file.",
                }
            )


        # ----------------------------------------------------
        # Check extension
        # ----------------------------------------------------

        if not pdf_file.name.lower().endswith(
            ".pdf"
        ):

            return render(
                request,
                "pdf_overlay/overlay.html",
                {
                    "overlay_images": overlay_images,
                    "default_overlay": default_overlay,
                    "error": "Only PDF files are allowed.",
                }
            )


        # ====================================================
        # GET SELECTED OVERLAY
        # ====================================================

        overlay_id = request.POST.get(
            "overlay_image"
        )


        if not overlay_id:

            return render(
                request,
                "pdf_overlay/overlay.html",
                {
                    "overlay_images": overlay_images,
                    "default_overlay": default_overlay,
                    "error": "Please select an overlay image.",
                }
            )


        # ====================================================
        # GET OVERLAY OBJECT
        # ====================================================

        try:

            overlay = OverlayImage.objects.get(
                pk=overlay_id
            )

        except OverlayImage.DoesNotExist:

            return render(
                request,
                "pdf_overlay/overlay.html",
                {
                    "overlay_images": overlay_images,
                    "default_overlay": default_overlay,
                    "error": "Selected overlay image was not found.",
                }
            )


        # ====================================================
        # GET POSITION
        # ====================================================

        position = request.POST.get(
            "position",
            "bottom_center"
        )


        # ====================================================
        # ALLOWED POSITIONS
        # ====================================================

        allowed_positions = {
            "bottom_left",
            "bottom_center",
            "bottom_right",
            "top_left",
            "top_center",
            "top_right",
            "center",
        }


        if position not in allowed_positions:

            position = "bottom_center"


        # ====================================================
        # PROCESS PDF
        # ====================================================

        try:

            result = apply_overlay(
                pdf_file=pdf_file,
                image_path=overlay.image.path,
                position=position,
            )

        except Exception as error:

            return render(
                request,
                "pdf_overlay/overlay.html",
                {
                    "overlay_images": overlay_images,
                    "default_overlay": default_overlay,
                    "error": (
                        f"Unable to process PDF: {error}"
                    ),
                }
            )


        # ====================================================
        # DOWNLOAD
        # ====================================================

        return FileResponse(
            result,
            as_attachment=True,
            filename="pdf_overlay_result.pdf",
            content_type="application/pdf",
        )


    # ========================================================
    # GET REQUEST
    # ========================================================

    return render(
        request,
        "dashboard/overlay.html",
        {
            "overlay_images": overlay_images,
            "default_overlay": default_overlay,
        }
    )