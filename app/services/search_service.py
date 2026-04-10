from app.repositories.track_repo import TrackRepository


class SearchService:

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
                        "file_url": track.file_url,
                    }
                    for track in tracks
                ]
            },
        }
