import pytest
from pathlib import Path
from agenttoast.agents.delivery import DeliveryAgent, DeliveryStatus

def test_delivery_agent_initialization():
    """Test DeliveryAgent initialization."""
    agent = DeliveryAgent()
    assert agent is not None
    assert isinstance(agent, DeliveryAgent)

def test_email_delivery(test_output_dir):
    """Test email delivery functionality."""
    agent = DeliveryAgent()
    test_digest = {
        "digest_id": "test123",
        "user_id": "user123",
        "content": "Test digest content",
        "audio_path": str(Path(test_output_dir) / "test_audio.mp3")
    }
    
    # Create a dummy audio file
    Path(test_digest["audio_path"]).touch()
    
    status = agent.deliver_via_email(
        test_digest,
        to_email="test@example.com"
    )
    assert isinstance(status, DeliveryStatus)
    assert status.digest_id == test_digest["digest_id"]
    assert status.user_id == test_digest["user_id"]
    assert status.delivery_method == "email"

def test_s3_delivery(test_output_dir):
    """Test S3 delivery functionality."""
    agent = DeliveryAgent()
    test_digest = {
        "digest_id": "test123",
        "user_id": "user123",
        "content": "Test digest content",
        "audio_path": str(Path(test_output_dir) / "test_audio.mp3")
    }
    
    # Create a dummy audio file
    Path(test_digest["audio_path"]).touch()
    
    status = agent.deliver_via_s3(
        test_digest,
        bucket_name="test-bucket"
    )
    assert isinstance(status, DeliveryStatus)
    assert status.digest_id == test_digest["digest_id"]
    assert status.user_id == test_digest["user_id"]
    assert status.delivery_method == "s3"

def test_delivery_status_tracking():
    """Test delivery status tracking functionality."""
    status = DeliveryStatus(
        digest_id="test123",
        user_id="user123",
        delivery_method="email",
        status="success",
        timestamp="2024-03-14T12:00:00Z"
    )
    
    assert status.digest_id == "test123"
    assert status.user_id == "user123"
    assert status.delivery_method == "email"
    assert status.status == "success"
    assert status.retry_count == 0
    assert status.error_message is None

def test_delivery_retry_mechanism(test_output_dir):
    """Test delivery retry mechanism."""
    agent = DeliveryAgent()
    test_digest = {
        "digest_id": "test123",
        "user_id": "user123",
        "content": "Test digest content",
        "audio_path": str(Path(test_output_dir) / "test_audio.mp3")
    }
    
    # Create a dummy audio file
    Path(test_digest["audio_path"]).touch()
    
    # Simulate a failed delivery with retry
    status = agent.deliver_via_email(
        test_digest,
        to_email="invalid@example.com"
    )
    assert status.retry_count > 0
    assert status.error_message is not None

def test_run_delivery_process(test_output_dir):
    """Test complete delivery process."""
    agent = DeliveryAgent()
    test_digests = [
        {
            "digest_id": f"test{i}",
            "user_id": f"user{i}",
            "content": f"Test content {i}",
            "audio_path": str(Path(test_output_dir) / f"audio_{i}.mp3")
        }
        for i in range(2)
    ]
    
    # Create dummy audio files
    for digest in test_digests:
        Path(digest["audio_path"]).touch()
    
    delivery_results = agent.run(
        digests=test_digests,
        delivery_methods=["email", "s3"]
    )
    
    assert isinstance(delivery_results, list)
    assert len(delivery_results) == len(test_digests) * 2  # Two methods per digest
    assert all(isinstance(result, DeliveryStatus) for result in delivery_results) 