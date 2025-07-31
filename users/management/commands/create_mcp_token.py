import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.mcp import MCPToken
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a new MCP token for a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to create token for')
        parser.add_argument('--name', type=str, default='API Access', help='Name for the token')
        parser.add_argument('--days', type=int, default=365, help='Days until token expires')

    def handle(self, *args, **options):
        username = options['username']
        token_name = options['name']
        days = options['days']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'User {username} does not exist'))
            return

        # Create token
        token = MCPToken(
            user=user,
            name=token_name,
            expires_at=timezone.now() + timedelta(days=days)
        )
        token.save()

        self.stdout.write(self.style.SUCCESS(f'Token created successfully!'))
        self.stdout.write(f'Token value: {token.token}')
        self.stdout.write(f'Expires on: {token.expires_at.strftime("%Y-%m-%d")}')

        # Provide the MCP config snippet
        self.stdout.write('\nMCP Configuration:')
        mcp_config = {
          "servers": {
            "my-django-mcp": {
              "type": "http",
              "url": "http://127.0.0.1:8000/api/mcp/",
              "requestInit": {
                "headers": {
                  "Authorization": f"Bearer {token.token}"
                }
              }
            }
          }
        }
        import json
        self.stdout.write(json.dumps(mcp_config, indent=2))
