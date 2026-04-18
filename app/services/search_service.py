from app.repositories.playlist_repo import PlaylistRepository
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

        def serialize_track(track):
            release_date = getattr(track, "release_date", None)

            return {
                "track_id": str(track.track_id),
                "title": track.title,
                "description": track.description,
                "genre": getattr(track, "genre", None),
                "tags": getattr(track, "tags", None) or [],
                "release_date": (release_date.isoformat() if release_date else None),
                "file_url": track.file_url,
                "visibility": getattr(track, "visibility", None) or "public",
                "processing_status": (
                    getattr(track, "processing_status", None) or "finished"
                ),
            }

        return {
            "success": True,
            "data": {"tracks": [serialize_track(track) for track in tracks]},
        }

    @staticmethod
    def search_playlists(db, keyword: str):
        playlists = PlaylistRepository.search_by_name(db, keyword)

        playlist_results = []
        for playlist in playlists:
            playlist_tracks = PlaylistRepository.get_playlist_tracks(
                db, playlist.playlist_id
            )
            tracks = []

            for playlist_track in playlist_tracks:
                track = TrackRepository.get_by_id(db, playlist_track.track_id)
                if track:
                    tracks.append(
                        {
                            "track_id": str(track.track_id),
                            "user_id": str(track.user_id),
                            "title": track.title,
                            "description": track.description,
                            "genre": track.genre,
                            "tags": track.tags,
                            "release_date": track.release_date,
                            "file_url": track.file_url,
                            "visibility": track.visibility,
                            "play_count": track.play_count,
                            "duration_seconds": track.duration_seconds,
                        }
                    )

            playlist_results.append(
                {
                    "playlist_id": str(playlist.playlist_id),
                    "user_id": str(playlist.user_id),
                    "name": playlist.name,
                    "description": playlist.description,
                    "cover_photo_url": playlist.cover_photo_url,
                    "tracks": tracks,
                }
            )

        return {
            "success": True,
            "data": {"playlists": playlist_results},
        }
