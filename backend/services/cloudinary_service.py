import cloudinary
import cloudinary.api
import cloudinary.uploader

cloudinary.config(secure=True)


def upload_media(file, public_id):
    try:
        res = cloudinary.uploader.upload(
            file=file,
            public_id=public_id,
            overwrite=True,
            resource_type="auto",
        )
        return res
    except Exception as e:
        print(f"Error uploading media: {e}")
        raise Exception(e)


def delete_media(public_id: list[str]):
    try:
        res = cloudinary.api.delete_resources(public_ids=public_id)
        return res
    except Exception as e:
        print(f"Error deleting media: {e}")
        raise Exception(e)
