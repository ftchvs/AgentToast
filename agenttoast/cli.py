"""
Command-line interface for AgentToast.
Provides commands for managing users and generating digests.
"""

import click
from pathlib import Path
import uuid
from datetime import datetime

from agenttoast.core.user import UserManager, UserPreferences
from agenttoast.tasks.workers import process_user_digest

@click.group()
def cli():
    """AgentToast CLI - Manage your news digest service."""
    pass

@cli.group()
def users():
    """Manage users."""
    pass

@users.command()
@click.argument('name')
def create(name):
    """Create a new user."""
    user_id = str(uuid.uuid4())[:8]
    manager = UserManager()
    try:
        user = manager.create_user(user_id, name)
        click.echo(f"Created user {user.name} with ID: {user.user_id}")
        click.echo("Default preferences:")
        for key, value in user.preferences.model_dump().items():
            click.echo(f"  {key}: {value}")
    except Exception as e:
        click.echo(f"Error creating user: {e}", err=True)

@users.command()
@click.argument('user_id')
def show(user_id):
    """Show user details."""
    manager = UserManager()
    try:
        user = manager.get_user(user_id)
        if not user:
            click.echo(f"User {user_id} not found", err=True)
            return
        
        click.echo(f"User: {user.name} ({user.user_id})")
        click.echo("\nPreferences:")
        for key, value in user.preferences.model_dump().items():
            click.echo(f"  {key}: {value}")
        
        click.echo("\nRecent digests:")
        for digest in manager.get_user_digests(user_id, limit=5):
            click.echo(f"  {digest.timestamp}: {len(digest.stories)} stories, {digest.duration:.1f}s")
    except Exception as e:
        click.echo(f"Error showing user: {e}", err=True)

@users.command()
@click.argument('user_id')
@click.option('--categories', '-c', help='Comma-separated list of categories')
@click.option('--sources', '-s', help='Comma-separated list of sources')
@click.option('--max-stories', '-m', type=int, help='Maximum number of stories')
@click.option('--voice-id', '-v', help='Voice ID for audio generation')
@click.option('--delivery-time', '-t', help='Delivery time (HH:MM)')
@click.option('--language', '-l', help='Language code')
def update(user_id, categories, sources, max_stories, voice_id, delivery_time, language):
    """Update user preferences."""
    manager = UserManager()
    try:
        user = manager.get_user(user_id)
        if not user:
            click.echo(f"User {user_id} not found", err=True)
            return
        
        prefs = user.preferences.model_dump()
        if categories:
            prefs['categories'] = categories.split(',')
        if sources:
            prefs['sources'] = sources.split(',')
        if max_stories:
            prefs['max_stories'] = max_stories
        if voice_id:
            prefs['voice_id'] = voice_id
        if delivery_time:
            prefs['delivery_time'] = delivery_time
        if language:
            prefs['language'] = language
        
        new_prefs = UserPreferences(**prefs)
        manager.update_preferences(user_id, new_prefs)
        click.echo(f"Updated preferences for user {user.name}")
    except Exception as e:
        click.echo(f"Error updating preferences: {e}", err=True)

@cli.group()
def digest():
    """Manage digests."""
    pass

@digest.command()
@click.argument('user_id')
def generate(user_id):
    """Generate a digest for a user."""
    manager = UserManager()
    try:
        user = manager.get_user(user_id)
        if not user:
            click.echo(f"User {user_id} not found", err=True)
            return
        
        click.echo(f"Generating digest for {user.name}...")
        task = process_user_digest.delay(user_id)
        click.echo(f"Task started: {task.id}")
        click.echo("Use 'status' command to check progress")
    except Exception as e:
        click.echo(f"Error generating digest: {e}", err=True)

@digest.command()
@click.argument('user_id')
def list(user_id):
    """List user's digests."""
    manager = UserManager()
    try:
        digests = manager.get_user_digests(user_id)
        if not digests:
            click.echo("No digests found")
            return
        
        for digest in digests:
            click.echo(f"\nDigest {digest.digest_id}")
            click.echo(f"  Generated: {digest.timestamp}")
            click.echo(f"  Stories: {len(digest.stories)}")
            click.echo(f"  Duration: {digest.duration:.1f}s")
            click.echo(f"  Audio: {digest.audio_path}")
            click.echo(f"  Summary: {digest.summary_path}")
    except Exception as e:
        click.echo(f"Error listing digests: {e}", err=True)

if __name__ == '__main__':
    cli() 