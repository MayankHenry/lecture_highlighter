from app.services.cloudinary_svc import upload_video, clip_url

public_id, url = upload_video("sample.mp4")
print("Uploaded:", url)
print("Clip 5s-15s:", clip_url(public_id, 5, 15))