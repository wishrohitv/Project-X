def fname(file_id: str | None, extension: str | None, post=False) -> str:
    """
    Returns the file name based on the file_id and extension.
    If either is None, returns "default".

    Args:
        file_id (str | None): The file ID.
        extension (str | None): The file extension.
        post (bool): Whether the file is a post or not.

    Returns:
        str: The file name.
    """
    if not file_id or not extension:
        if post:
            return "null"
        return "default"
    return f"{file_id}.{extension}"
