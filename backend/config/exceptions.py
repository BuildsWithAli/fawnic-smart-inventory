from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Wrap DRF's default handler to guarantee a consistent, human-readable error shape."""
    response = exception_handler(exc, context)

    if response is not None:
        detail = response.data
        if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
            message = detail["detail"]
        elif isinstance(detail, dict):
            first_key = next(iter(detail))
            first_value = detail[first_key]
            if isinstance(first_value, list) and first_value:
                message = f"{first_key}: {first_value[0]}"
            else:
                message = f"{first_key}: {first_value}"
        elif isinstance(detail, list) and detail:
            message = detail[0]
        else:
            message = "An error occurred."

        response.data = {"error": message, "detail": detail}

    return response
