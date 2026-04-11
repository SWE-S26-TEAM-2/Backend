from app.repositories.track_repo import TrackRepository
from app.repositories.playlist_repo import PlaylistRepository
from app.repositories.user_repo import UserRepository


class SearchService:

    @staticmethod
    def global_search(db, keyword: str):
        tracks = TrackRepository.search_by_title(db, keyword)
        playlists = PlaylistRepository.search_by_name(db, keyword)
        users = UserRepository.search_by_display_name(db, keyword)

        return {
            "success": True,
            "data": {
                "tracks": [
                    {
                        "track_id": str(track.track_id),
                        "title": track.title,
                        "description": track.description,
                        "file_url": track.file_url,
                    }
                    for track in tracks
                ],
                "playlists": [
                    {
                        "playlist_id": str(playlist.playlist_id),
                        "name": playlist.name,
                        "description": playlist.description,
                        "is_public": playlist.is_public,
                    }
                    for playlist in playlists
                ],
                "users": [
                    {
                        "user_id": str(user.user_id),
                        "display_name": user.display_name,
                        "email": user.email,
                    }
                    for user in users
                ],
            },
        }
