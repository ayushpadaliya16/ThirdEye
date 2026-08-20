from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, List, Any
from .text_sanitizer import TextSanitizer

class SocialProfileSchema(BaseModel):
    target_handle: str = Field(..., description="The handle or username of the target")
    platform: str = Field(..., description="The social media platform (e.g., twitter, instagram)")
    account_creation_date: Optional[str] = Field(None, description="Date the account was created, if available")
    follower_count: int = Field(0, description="Number of followers")
    following_count: int = Field(0, description="Number of accounts the target is following")
    bio_text: str = Field("", description="The profile biography text")
    recent_posts: List[str] = Field(default_factory=list, description="A list of recent posts/tweets")
    profile_picture_url: Optional[str] = Field(None, description="URL to the high-res profile picture")

    @field_validator("bio_text", mode="before")
    @classmethod
    def sanitize_bio(cls, v: Any) -> str:
        """Validates and sanitizes the bio text."""
        if not isinstance(v, str):
            v = str(v) if v is not None else ""
        return TextSanitizer.clean_text(v)

    @field_validator("recent_posts", mode="before")
    @classmethod
    def sanitize_posts(cls, v: Any) -> List[str]:
        """Validates and sanitizes the list of recent posts."""
        if not isinstance(v, list):
            return []
        return [TextSanitizer.clean_text(str(post)) for post in v if post]

    @field_validator("follower_count", "following_count", mode="before")
    @classmethod
    def parse_counts(cls, v: Any) -> int:
        """Ensures string metrics are converted to integers before validation."""
        return TextSanitizer.parse_metric(v)

    @computed_field
    def follower_to_following_ratio(self) -> float:
        """
        Calculates the ratio of followers to following. 
        Returns 0.0 if following_count is 0 to avoid division by zero.
        """
        if self.following_count == 0:
            # Handle division by zero gracefully.
            return float(self.follower_count) if self.follower_count > 0 else 0.0
        return round(self.follower_count / self.following_count, 4)
