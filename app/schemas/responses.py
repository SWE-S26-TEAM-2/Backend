from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict

# ── Shared ─────────────────────────────────────────────────────────────────────


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"success": True, "message": "Operation completed successfully."}
        }
    )

    success: bool
    message: str


class UnfollowResponse(BaseModel):
    success: bool
    message: str
    username: str


# ── Auth ───────────────────────────────────────────────────────────────────────


class RegisterData(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "email": "user@example.com",
                "username": "john_doe",
                "display_name": "John Doe",
                "is_verified": False,
            }
        }
    )

    user_id: str
    email: str
    username: str
    display_name: str
    is_verified: bool


class RegisterResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Registration successful. Please verify your email.",
                "data": {
                    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "email": "user@example.com",
                    "username": "john_doe",
                    "display_name": "John Doe",
                    "is_verified": False,
                },
            }
        }
    )

    success: bool
    message: str
    data: RegisterData


class CheckEmailResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"success": True, "available": True, "isExisting": False}
        }
    )

    success: bool
    available: bool
    isExisting: bool


class VerifyResetTokenResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"success": True, "valid": True, "message": "Token is valid."}
        }
    )

    success: bool
    valid: bool
    message: str


_USER_INFO_EXAMPLE = {
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "username": "john_doe",
    "display_name": "John Doe",
    "account_type": "listener",
    "is_premium": False,
}

_TOKEN_EXAMPLE = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
    "token_type": "bearer",
    "expires_in": 1800,
}


class UserInfo(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": _USER_INFO_EXAMPLE})

    user_id: str
    username: str
    display_name: str
    account_type: str
    is_premium: bool
    billing_cycle: Optional[str] = None


class LoginData(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {**_TOKEN_EXAMPLE, "user": _USER_INFO_EXAMPLE}}
    )

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserInfo


class LoginResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {**_TOKEN_EXAMPLE, "user": _USER_INFO_EXAMPLE},
            }
        }
    )

    success: bool
    data: LoginData


class SocialLoginData(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                **_TOKEN_EXAMPLE,
                "is_new_user": False,
                "user": _USER_INFO_EXAMPLE,
            }
        }
    )

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    is_new_user: bool
    user: UserInfo


class SocialLoginResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    **_TOKEN_EXAMPLE,
                    "is_new_user": False,
                    "user": _USER_INFO_EXAMPLE,
                },
            }
        }
    )

    success: bool
    data: SocialLoginData


class RefreshData(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": _TOKEN_EXAMPLE})

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"success": True, "data": _TOKEN_EXAMPLE}
        }
    )

    success: bool
    data: RefreshData


# ── User Profile ───────────────────────────────────────────────────────────────


class UserProfileData(BaseModel):
    user_id: str
    email: str
    username: str
    display_name: str
    account_type: str
    is_verified: bool
    is_suspended: bool
    bio: Optional[str] = None
    location: Optional[str] = None
    is_premium: bool
    billing_cycle: Optional[str] = None
    is_private: bool
    profile_picture: Optional[str] = None
    cover_photo: Optional[str] = None
    follower_count: int
    following_count: int
    track_count: int
    created_at: Optional[datetime] = None


class UserProfileResponse(BaseModel):
    success: bool
    data: UserProfileData


class PublicUserProfileData(BaseModel):
    user_id: str
    username: str
    display_name: str
    account_type: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    is_premium: Optional[bool] = None
    billing_cycle: Optional[str] = None
    profile_picture: Optional[str] = None
    cover_photo: Optional[str] = None
    follower_count: int
    following_count: Optional[int] = None
    track_count: Optional[int] = None
    is_private: Optional[bool] = None


class PublicUserProfileResponse(BaseModel):
    success: bool
    data: PublicUserProfileData


class AvatarData(BaseModel):
    profile_picture: str


class AvatarResponse(BaseModel):
    success: bool
    message: str
    data: AvatarData


class CoverData(BaseModel):
    cover_photo: str


class CoverResponse(BaseModel):
    success: bool
    message: str
    data: CoverData


class UsernameData(BaseModel):
    username: str


class UsernameResponse(BaseModel):
    success: bool
    data: UsernameData


class PrivacyData(BaseModel):
    is_private: bool


class PrivacyResponse(BaseModel):
    success: bool
    message: str
    data: PrivacyData


class SocialLinkItem(BaseModel):
    platform: str
    url: str


class SocialLinksData(BaseModel):
    social_links: List[SocialLinkItem]


class SocialLinksResponse(BaseModel):
    success: bool
    data: SocialLinksData


class HistoryTrackData(BaseModel):
    track_id: str
    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    stream_url: str
    duration_seconds: Optional[int] = None
    play_count: int


class HistoryItem(BaseModel):
    history_id: str
    played_at: Optional[datetime] = None
    duration_listened_seconds: Optional[int] = None
    track: HistoryTrackData


class ListeningHistoryData(BaseModel):
    items: List[HistoryItem]


class ListeningHistoryResponse(BaseModel):
    success: bool
    data: ListeningHistoryData


# ── Tracks ─────────────────────────────────────────────────────────────────────


class TrackData(BaseModel):
    track_id: str
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[List[Any]] = None
    release_date: Optional[str] = None
    cover_image_url: Optional[str] = None
    stream_url: str
    user_id: str
    visibility: str
    processing_status: str
    play_count: int
    duration_seconds: Optional[int] = None


class TrackResponse(BaseModel):
    success: bool
    data: TrackData


class TrackListResponse(BaseModel):
    success: bool
    data: List[TrackData]


class UserTracksData(BaseModel):
    user_id: str
    tracks: List[TrackData]


class UserTracksResponse(BaseModel):
    success: bool
    data: UserTracksData


class UpdateProfileData(BaseModel):
    user_id: str
    username: str
    display_name: str
    bio: Optional[str] = None
    location: Optional[str] = None
    account_type: str
    updated_at: Optional[datetime] = None


class UpdateProfileResponse(BaseModel):
    success: bool
    message: str
    data: UpdateProfileData


class TrackCreateData(BaseModel):
    track_id: str
    title: str
    genre: Optional[str] = None
    tags: Optional[List[Any]] = None
    release_date: Optional[str] = None
    cover_image_url: Optional[str] = None
    stream_url: str
    visibility: str
    processing_status: str


class TrackCreateResponse(BaseModel):
    success: bool
    message: str
    data: TrackCreateData


class WaveformData(BaseModel):
    track_id: str
    duration_seconds: Optional[int] = None
    sample_count: int
    peaks: List[float]


class WaveformResponse(BaseModel):
    success: bool
    data: WaveformData


class StreamData(BaseModel):
    track_id: str
    stream_url: str
    expires_in: Optional[int] = None
    content_type: str
    play_count: int
    processing_status: str


class StreamResponse(BaseModel):
    success: bool
    data: StreamData


class PlayData(BaseModel):
    track_id: str
    play_count: int


class PlayResponse(BaseModel):
    success: bool
    message: str
    data: PlayData


class PlaybackWaveform(BaseModel):
    sample_count: int
    peaks: List[float]


class PlaybackData(BaseModel):
    track_id: str
    title: str
    description: Optional[str] = None
    stream_url: str
    cover_image_url: Optional[str] = None
    expires_in: Optional[int] = None
    content_type: str
    play_count: int
    processing_status: str
    genre: Optional[str] = None
    tags: Optional[List[Any]] = None
    release_date: Optional[str] = None
    duration_seconds: Optional[int] = None
    waveform: PlaybackWaveform


class PlaybackResponse(BaseModel):
    success: bool
    data: PlaybackData


# ── Playlists ──────────────────────────────────────────────────────────────────


class PlaylistData(BaseModel):
    playlist_id: str
    name: str
    description: Optional[str] = None
    cover_photo_url: Optional[str] = None


class PlaylistResponse(BaseModel):
    success: bool
    message: str
    data: PlaylistData


class PlaylistUserData(BaseModel):
    playlist_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    cover_photo_url: Optional[str] = None


class PlaylistListResponse(BaseModel):
    success: bool
    data: List[PlaylistUserData]


class PlaylistTrackData(BaseModel):
    track_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[Any] = None
    release_date: Optional[Any] = None
    stream_url: str
    cover_image_url: Optional[str] = None
    visibility: str
    play_count: Optional[int] = None
    duration_seconds: Optional[int] = None


class PlaylistDetailData(BaseModel):
    playlist_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    cover_photo_url: Optional[str] = None
    tracks: List[PlaylistTrackData]


class PlaylistDetailResponse(BaseModel):
    success: bool
    data: PlaylistDetailData


class PlaylistUpdateData(BaseModel):
    playlist_id: str
    name: str
    description: Optional[str] = None


class PlaylistUpdateResponse(BaseModel):
    success: bool
    message: str
    data: PlaylistUpdateData


class PlaylistLikeData(BaseModel):
    playlist_like_id: str
    playlist_id: str


class PlaylistLikeResponse(BaseModel):
    success: bool
    message: str
    data: PlaylistLikeData


class PlaylistCoverData(BaseModel):
    playlist_id: str
    cover_photo_url: str


class PlaylistCoverResponse(BaseModel):
    success: bool
    message: str
    data: PlaylistCoverData


# ── Followers / Social Graph ───────────────────────────────────────────────────


class FollowResponse(BaseModel):
    success: bool
    message: str
    is_pending: bool


class FollowRequestItem(BaseModel):
    request_id: str
    requester_id: str
    requester_username: str
    requester_display_name: str
    requester_profile_picture: Optional[str] = None
    requested_at: Optional[datetime] = None


class FollowRequestListData(BaseModel):
    requests: List[FollowRequestItem]
    count: int


class FollowRequestListResponse(BaseModel):
    success: bool
    data: FollowRequestListData


class FollowerItem(BaseModel):
    user_id: str
    display_name: str
    is_premium: bool = False
    billing_cycle: Optional[str] = None
    profile_picture: Optional[str] = None
    followed_at: Optional[datetime] = None


class FollowerListData(BaseModel):
    count: int
    followers: List[FollowerItem]
    private: bool = False


class FollowerListResponse(BaseModel):
    success: bool
    data: FollowerListData


class FollowingItem(BaseModel):
    user_id: str
    display_name: str
    is_premium: bool = False
    billing_cycle: Optional[str] = None
    profile_picture: Optional[str] = None
    followed_at: Optional[datetime] = None


class FollowingListData(BaseModel):
    count: int
    following: List[FollowingItem]
    private: bool = False


class FollowingListResponse(BaseModel):
    success: bool
    data: FollowingListData


# ── Engagement ─────────────────────────────────────────────────────────────────


class LikeData(BaseModel):
    like_id: str
    track_id: str


class LikeResponse(BaseModel):
    success: bool
    message: str
    data: LikeData


class TrackLikeCountData(BaseModel):
    track_id: str
    like_count: int


class TrackLikeCountResponse(BaseModel):
    success: bool
    data: TrackLikeCountData


class TrackEngagementSummaryData(BaseModel):
    track_id: str
    like_count: int
    comment_count: int
    repost_count: int
    liked_by_me: Optional[bool] = None
    reposted_by_me: Optional[bool] = None


class TrackEngagementSummaryResponse(BaseModel):
    success: bool
    data: TrackEngagementSummaryData


class RepostData(BaseModel):
    repost_id: str
    track_id: str


class RepostResponse(BaseModel):
    success: bool
    message: str
    data: RepostData


class UserRepostItem(BaseModel):
    repost_id: str
    track_id: str
    title: str
    stream_url: str
    cover_image_url: Optional[str] = None
    reposted_at: Optional[datetime] = None


class UserRepostsData(BaseModel):
    username: str
    reposts: List[UserRepostItem]


class UserRepostsResponse(BaseModel):
    success: bool
    data: UserRepostsData


class CommentItem(BaseModel):
    comment_id: str
    user_id: str
    content: str
    timestamp_in_track: Optional[float] = None
    parent_comment_id: Optional[str] = None
    created_at: Optional[datetime] = None


class CommentsData(BaseModel):
    comments: List[CommentItem]


class CommentsListResponse(BaseModel):
    success: bool
    data: CommentsData


class AddCommentData(BaseModel):
    comment_id: str
    track_id: str
    content: str
    timestamp_in_track: Optional[float] = None
    parent_comment_id: Optional[str] = None
    created_at: Optional[datetime] = None


class AddCommentResponse(BaseModel):
    success: bool
    message: str
    data: AddCommentData


# ── Search ─────────────────────────────────────────────────────────────────────


class ReportSubmissionData(BaseModel):
    report_id: str
    entity_type: str
    entity_id: str
    status: str
    created_at: Optional[datetime] = None


class ReportSubmissionResponse(BaseModel):
    success: bool
    message: str
    data: ReportSubmissionData


class AdminActorData(BaseModel):
    user_id: str
    username: str
    display_name: str


class AdminReportItem(BaseModel):
    report_id: str
    entity_type: str
    entity_id: str
    reason: str
    status: str
    created_at: Optional[datetime] = None
    reporter: AdminActorData
    reviewed_by: Optional[AdminActorData] = None
    reviewed_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    entity_preview: Optional[dict[str, Any]] = None


class AdminReportsData(BaseModel):
    total: int
    reports: List[AdminReportItem]


class AdminReportsResponse(BaseModel):
    success: bool
    data: AdminReportsData


class AdminReportReviewResponse(BaseModel):
    success: bool
    message: str
    data: AdminReportItem


class AdminAnalyticsData(BaseModel):
    total_users: int
    total_tracks: int
    total_comments: int
    total_reports: int
    open_reports: int
    under_review_reports: int
    resolved_reports: int
    dismissed_reports: int
    suspended_users: int
    active_streams_today: int


class AdminAnalyticsResponse(BaseModel):
    success: bool
    data: AdminAnalyticsData


class AdminUserModerationData(BaseModel):
    user_id: str
    username: str
    display_name: str
    is_suspended: bool
    reason: Optional[str] = None


class AdminUserModerationResponse(BaseModel):
    success: bool
    message: str
    data: AdminUserModerationData


class AdminTrackModerationData(BaseModel):
    track_id: str
    title: str


class AdminTrackModerationResponse(BaseModel):
    success: bool
    message: str
    data: AdminTrackModerationData


class AdminUserRoleData(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: str


class AdminUserRoleResponse(BaseModel):
    success: bool
    message: str
    data: AdminUserRoleData


class AdminBootstrapData(BaseModel):
    user_id: str
    email: str
    username: str
    display_name: str
    role: str
    is_verified: bool


class AdminBootstrapResponse(BaseModel):
    success: bool
    message: str
    data: AdminBootstrapData


class SearchUserItem(BaseModel):
    user_id: str
    username: str
    display_name: str
    account_type: str
    profile_picture: Optional[str] = None
    follower_count: int
    is_verified: bool
    is_premium: bool = False
    billing_cycle: Optional[str] = None
    is_following: bool = False


class SearchUsersData(BaseModel):
    users: List[SearchUserItem]


class SearchUsersResponse(BaseModel):
    success: bool
    query_time_ms: Optional[float] = None
    data: SearchUsersData


class SearchUsersOptimizedResponse(BaseModel):
    success: bool
    optimized: bool
    query_time_ms: float
    result_count: int
    data: SearchUsersData


class SearchTrackItem(BaseModel):
    track_id: str
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[List[Any]] = None
    release_date: Optional[str] = None
    stream_url: str
    cover_image_url: Optional[str] = None
    visibility: str
    processing_status: str


class SearchTracksData(BaseModel):
    tracks: List[SearchTrackItem]


class SearchTracksResponse(BaseModel):
    success: bool
    query_time_ms: Optional[float] = None
    data: SearchTracksData


class SearchTracksOptimizedResponse(BaseModel):
    success: bool
    optimized: bool
    query_time_ms: float
    result_count: int
    data: SearchTracksData


class SearchPlaylistItem(BaseModel):
    playlist_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    cover_photo_url: Optional[str] = None
    tracks: List[PlaylistTrackData]


class SearchPlaylistsData(BaseModel):
    playlists: List[SearchPlaylistItem]


class SearchPlaylistsResponse(BaseModel):
    success: bool
    query_time_ms: Optional[float] = None
    data: SearchPlaylistsData


class SearchPlaylistsOptimizedResponse(BaseModel):
    success: bool
    optimized: bool
    query_time_ms: float
    result_count: int
    data: SearchPlaylistsData


class SearchAlbumItem(BaseModel):
    album_id: str
    title: str
    year: Optional[int] = None
    artist_name: str
    cover_photo_url: Optional[str] = None
    like_count: int
    track_count: int


class SearchAlbumsData(BaseModel):
    albums: List[SearchAlbumItem]


class SearchAlbumsResponse(BaseModel):
    success: bool
    query_time_ms: Optional[float] = None
    data: SearchAlbumsData


# ── Notifications ──────────────────────────────────────────────────────────────


_NOTIFICATION_ITEM_EXAMPLE = {
    "notification_id": "b1c2d3e4-f5a6-7890-bcde-f12345678901",
    "actor_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "actor_username": "jane_doe",
    "actor_display_name": "Jane Doe",
    "actor_profile_picture": "https://cdn.example.com/avatars/jane_doe.jpg",
    "notification_type": "follow",
    "target_id": None,
    "message": "jane_doe started following you.",
    "is_read": False,
    "created_at": "2026-04-30T12:00:00Z",
}


class NotificationItem(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": _NOTIFICATION_ITEM_EXAMPLE})

    notification_id: str
    actor_id: str
    actor_username: str
    actor_display_name: str
    actor_profile_picture: Optional[str] = None
    notification_type: str
    target_id: Optional[str] = None
    message: str
    is_read: bool
    created_at: Optional[datetime] = None


class NotificationsData(BaseModel):
    notifications: List[NotificationItem]


class NotificationsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "notifications": [_NOTIFICATION_ITEM_EXAMPLE],
                },
            }
        }
    )

    success: bool
    data: NotificationsData


class UnreadCountData(BaseModel):
    unread_count: int


class UnreadCountResponse(BaseModel):
    success: bool
    data: UnreadCountData


class MarkReadData(BaseModel):
    notification_id: str
    is_read: bool


class MarkReadResponse(BaseModel):
    success: bool
    message: str
    data: MarkReadData


class MarkAllReadData(BaseModel):
    marked_read: int


class MarkAllReadResponse(BaseModel):
    success: bool
    message: str
    data: MarkAllReadData


# ── Messaging ──────────────────────────────────────────────────────────────────


class ConversationData(BaseModel):
    conversation_id: str


class ConversationResponse(BaseModel):
    success: bool
    data: ConversationData


class LastMessageData(BaseModel):
    content: Optional[str] = None
    sender_id: str
    created_at: Optional[datetime] = None
    is_read: bool


class ParticipantData(BaseModel):
    user_id: str
    display_name: str
    is_premium: bool = False
    billing_cycle: Optional[str] = None
    profile_picture: Optional[str] = None


class ConversationItem(BaseModel):
    conversation_id: str
    created_at: Optional[datetime] = None
    participants: List[ParticipantData]
    last_message: Optional[LastMessageData] = None


class ConversationsListResponse(BaseModel):
    success: bool
    data: List[ConversationItem]


class MessageItem(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: Optional[str] = None
    track_id: Optional[str] = None
    playlist_id: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None


class MessagesListResponse(BaseModel):
    success: bool
    data: List[MessageItem]


class SendMessageResponse(BaseModel):
    success: bool
    data: MessageItem


class MessageReadData(BaseModel):
    message_id: str
    is_read: bool


class MessageReadResponse(BaseModel):
    success: bool
    message: str
    data: MessageReadData


class UnreadMessageCountResponse(BaseModel):
    success: bool
    data: UnreadCountData


# ── Feed ───────────────────────────────────────────────────────────────────────


class FeedArtist(BaseModel):
    user_id: str
    username: str
    display_name: str
    is_premium: bool = False
    billing_cycle: Optional[str] = None
    profile_picture: Optional[str] = None
    follower_count: int


class FeedTrackItem(BaseModel):
    track_id: str
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[List[Any]] = None
    release_date: Optional[str] = None
    cover_image_url: Optional[str] = None
    stream_url: str
    duration_seconds: Optional[int] = None
    play_count: int
    like_count: int
    repost_count: int
    comment_count: int
    is_liked: bool
    is_reposted: bool
    created_at: Optional[datetime] = None
    artist: FeedArtist


class FeedData(BaseModel):
    items: List[FeedTrackItem]
    next_cursor: Optional[str] = None
    has_more: bool


class FeedResponse(BaseModel):
    success: bool
    query_time_ms: Optional[float] = None
    data: FeedData


class CachedFeedResponse(BaseModel):
    success: bool
    optimized: bool
    cache_hit: bool
    query_time_ms: float
    cached_at: Optional[str] = None
    cache_ttl_seconds: int
    data: FeedData


class CacheClearResponse(BaseModel):
    success: bool
    message: str


# ── Albums ─────────────────────────────────────────────────────────────────────


class AlbumTrackItem(BaseModel):
    track_id: str
    title: str
    stream_url: str
    cover_image_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    play_count: int = 0
    position: int


class AlbumData(BaseModel):
    album_id: str
    title: str
    year: Optional[int] = None
    artist_name: str
    cover_photo_url: Optional[str] = None
    like_count: int
    track_count: int


class AlbumResponse(BaseModel):
    success: bool
    message: str
    data: AlbumData


class AlbumDetailData(BaseModel):
    album_id: str
    title: str
    year: Optional[int] = None
    artist_name: str
    cover_photo_url: Optional[str] = None
    like_count: int
    track_count: int
    tracks: List[AlbumTrackItem]


class AlbumDetailResponse(BaseModel):
    success: bool
    data: AlbumDetailData


class AlbumListItem(BaseModel):
    album_id: str
    title: str
    year: Optional[int] = None
    artist_name: str
    cover_photo_url: Optional[str] = None
    like_count: int
    track_count: int


class AlbumListResponse(BaseModel):
    success: bool
    data: List[AlbumListItem]


class AlbumUpdateData(BaseModel):
    album_id: str
    title: str
    year: Optional[int] = None


class AlbumUpdateResponse(BaseModel):
    success: bool
    message: str
    data: AlbumUpdateData


class AlbumLikeData(BaseModel):
    album_like_id: str
    album_id: str


class AlbumLikeResponse(BaseModel):
    success: bool
    message: str
    data: AlbumLikeData


class AlbumCoverData(BaseModel):
    album_id: str
    cover_photo_url: str


class AlbumCoverResponse(BaseModel):
    success: bool
    message: str
    data: AlbumCoverData
