from apps.accounts.models import UserAccount


USER_SESSION_KEY = "yaarlynx_user_id"
USER_ROLE = "yaarlynx_user_role"
USER_FIRSTNAME = "yaarlynx_user_firstname"
USER_LASTNAME = "yaarlynx_user_lastname"
USER_EMAIL = "yaarlynx_user_email"
USER_PROFILE = "yaarlynx_user_profile_link"

# ==========================================================
# LOGIN USER
# ==========================================================

def login_user(request, user):

    # Remove any previous session
    request.session.flush()

    # Store only custom user's UUID
    request.session[USER_SESSION_KEY] = str(user.id)
    request.session[USER_ROLE] = str(user.role)
    request.session[USER_FIRSTNAME] = str(user.first_name)
    request.session[USER_LASTNAME] = str(user.last_name)
    request.session[USER_EMAIL] = str(user.email)
    request.session[USER_PROFILE] = str(user.profile_image)

    # Save session
    request.session.save()


# ==========================================================
# LOGOUT USER
# ==========================================================

def logout_user(request):

    # Completely destroy current session
    request.session.flush()


# ==========================================================
# GET LOGGED-IN USER
# ==========================================================

def get_logged_in_user(request):

    # Get user ID from custom session
    user_id = request.session.get(
        USER_SESSION_KEY
    )

    if not user_id:
        return None


    # Find user using custom model
    try:

        user = UserAccount.objects.select_related(
            "role"
        ).get(
            id=user_id,
            is_active=True
        )

    except UserAccount.DoesNotExist:

        # Invalid/deleted/deactivated user
        request.session.flush()

        return None


    return user