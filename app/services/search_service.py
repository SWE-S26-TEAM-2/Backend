from app.repositories.track_repo import TrackRepository
from app.repositories.user_repo import UserRepository


class SearchService:

    @staticmethod
    def search_users(db, keyword: str):
        users = UserRepository.search_by_name(db, keyword)
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "user_id": str(u.user_id),
                        "display_name": u.display_name,
                        "account_type": u.account_type,
                        "profile_picture": u.profile_picture,
                        "follower_count": u.follower_count,
                        "is_verified": u.is_verified,
                    }
                    for u in users
                ]
            },
        }

    @staticmethod
    def search_tracks(db, keyword: str):
        tracks = TrackRepository.search_by_title(db, keyword)

        return {
            "success": True,
            "data": {
                "tracks": [
                    {
                        "track_id": str(track.track_id),
                        "title": track.title,
                        "description": track.description,
                        "genre": track.genre,
                        "tags": track.tags or [],
                        "release_date": (
                            track.release_date.isoformat()
                            if track.release_date
                            else None
                        ),
                        "file_url": track.file_url,
                        "visibility": track.visibility,
                        "processing_status": track.processing_status,
                    }
                    for track in tracks
                ]
            },
        }
