"""Delivery agent for distributing audio digests to users."""
from typing import Dict, List, Optional
from pathlib import Path
import smtplib
from email.mime.audio import MIMEAudio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import boto3
from datetime import datetime

from ..core.agent import Agent
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logger import logger
from .audio_gen import AudioDigest

settings = get_settings()

class DeliveryStatus(BaseModel):
    """Delivery status data model."""
    digest_id: str
    user_id: str
    delivery_method: str
    status: str
    timestamp: datetime
    retry_count: int = 0
    error_message: Optional[str] = None

class DeliveryAgent(Agent):
    """Agent for delivering audio digests to users."""

    def __init__(self):
        super().__init__()
        self.s3_client = None
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )

    async def deliver_via_email(self, digest: AudioDigest, user_email: str) -> DeliveryStatus:
        """Deliver audio digest via email.
        
        Args:
            digest: Audio digest to deliver
            user_email: Recipient email address
        
        Returns:
            DeliveryStatus: Delivery status
        """
        try:
            msg = MIMEMultipart()
            msg['Subject'] = f'Your Daily News Digest - {datetime.now().strftime("%Y-%m-%d")}'
            msg['From'] = settings.smtp_sender
            msg['To'] = user_email

            # Add text content
            text_content = "Here's your daily audio news digest.\n\nStories included:\n"
            for story in digest.stories:
                text_content += f"- {story.title} ({story.source})\n"
            msg.attach(MIMEText(text_content, 'plain'))

            # Attach audio file
            audio_attachment = MIMEAudio(digest.audio_data, _subtype=digest.format)
            audio_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=f'news_digest_{datetime.now().strftime("%Y%m%d")}.{digest.format}'
            )
            msg.attach(audio_attachment)

            # Send email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)

            return DeliveryStatus(
                digest_id=digest.digest_id,
                user_id=digest.user_id,
                delivery_method='email',
                status='delivered',
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error delivering digest via email: {str(e)}")
            return DeliveryStatus(
                digest_id=digest.digest_id,
                user_id=digest.user_id,
                delivery_method='email',
                status='failed',
                timestamp=datetime.now(),
                error_message=str(e)
            )

    async def deliver_via_s3(self, digest: AudioDigest, user_id: str) -> DeliveryStatus:
        """Deliver audio digest via S3.
        
        Args:
            digest: Audio digest to deliver
            user_id: User ID for S3 path
        
        Returns:
            DeliveryStatus: Delivery status
        """
        if not self.s3_client:
            return DeliveryStatus(
                digest_id=digest.digest_id,
                user_id=user_id,
                delivery_method='s3',
                status='failed',
                timestamp=datetime.now(),
                error_message='S3 client not configured'
            )

        try:
            # Upload to S3
            key = f'digests/{user_id}/{datetime.now().strftime("%Y/%m/%d")}/digest.{digest.format}'
            self.s3_client.put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=digest.audio_data,
                ContentType=f'audio/{digest.format}'
            )

            # Generate presigned URL
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.s3_bucket, 'Key': key},
                ExpiresIn=86400  # 24 hours
            )

            return DeliveryStatus(
                digest_id=digest.digest_id,
                user_id=user_id,
                delivery_method='s3',
                status='delivered',
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error delivering digest via S3: {str(e)}")
            return DeliveryStatus(
                digest_id=digest.digest_id,
                user_id=user_id,
                delivery_method='s3',
                status='failed',
                timestamp=datetime.now(),
                error_message=str(e)
            )

    async def run(self, digest: AudioDigest, user_id: str, delivery_methods: List[str]) -> List[DeliveryStatus]:
        """Run the delivery agent.
        
        Args:
            digest: Audio digest to deliver
            user_id: User ID
            delivery_methods: List of delivery methods to use
        
        Returns:
            List[DeliveryStatus]: List of delivery statuses
        """
        logger.info(f"Starting delivery for user {user_id}")
        
        statuses = []
        for method in delivery_methods:
            if method == 'email':
                user = self.user_manager.get_user(user_id)
                if user and user.email:
                    status = await self.deliver_via_email(digest, user.email)
                    statuses.append(status)
            elif method == 's3':
                status = await self.deliver_via_s3(digest, user_id)
                statuses.append(status)
            else:
                logger.warning(f"Unsupported delivery method: {method}")
        
        logger.info(
            f"Finished delivery attempts",
            extra={
                "successful": sum(1 for s in statuses if s.status == 'delivered'),
                "failed": sum(1 for s in statuses if s.status == 'failed')
            }
        )
        
        return statuses 