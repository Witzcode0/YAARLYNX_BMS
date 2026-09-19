from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from apps.dashboard.session import get_logged_in_user


# ==========================================================
# LOGIN REQUIRED
# ==========================================================

def login_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # --------------------------------------------------
        # GET CURRENT USER
        # --------------------------------------------------

        user = get_logged_in_user(request)


        # --------------------------------------------------
        # USER NOT LOGGED IN
        # --------------------------------------------------

        if user is None:

            messages.warning(
                request,
                "Please login first to continue."
            )

            return redirect(
                "login_view"
            )


        # --------------------------------------------------
        # STORE CURRENT USER
        # --------------------------------------------------

        request.current_user = user


        # --------------------------------------------------
        # RUN PROTECTED VIEW
        # --------------------------------------------------

        return view_func(
            request,
            *args,
            **kwargs
        )


    return wrapper


# ==========================================================
# DASHBOARD ACCESS REQUIRED
# ==========================================================

def dashboard_access_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # --------------------------------------------------
        # GET CURRENT USER
        # --------------------------------------------------

        user = get_logged_in_user(request)


        # --------------------------------------------------
        # USER NOT LOGGED IN
        # --------------------------------------------------

        if user is None:

            messages.warning(
                request,
                "Please login first to access the dashboard."
            )

            return redirect(
                "login_view"
            )


        # --------------------------------------------------
        # CHECK DASHBOARD ACCESS
        # --------------------------------------------------

        if not user.has_dashboard_access:

            messages.error(
                request,
                "You do not have permission to access the dashboard."
            )

            return redirect(
                "login_view"
            )


        # --------------------------------------------------
        # STORE CURRENT USER
        # --------------------------------------------------

        request.current_user = user


        # --------------------------------------------------
        # RUN PROTECTED VIEW
        # --------------------------------------------------

        return view_func(
            request,
            *args,
            **kwargs
        )


    return wrapper

