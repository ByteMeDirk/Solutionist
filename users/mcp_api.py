from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from solutions.models import Solution
from tags.models import Tag
from .mcp import MCPToken
import logging

logger = logging.getLogger(__name__)

def get_user_from_token(request):
    """
    Authenticate a user from the MCP token in the request header.
    """
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        return None

    token_string = auth_header.replace('Bearer ', '', 1).strip()

    try:
        token = MCPToken.objects.get(token=token_string)

        # Check if token is valid
        if not token.is_valid():
            return None

        # Update last used timestamp
        token.update_last_used()

        return token.user
    except MCPToken.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error authenticating MCP token: {str(e)}")
        return None


@csrf_exempt
def mcp_endpoint(request):
    """
    Main MCP endpoint for handling AI assistant interactions.
    Implements JSON-RPC 2.0 protocol for MCP compatibility.
    """
    # Handle GET requests for SSE connections
    if request.method == "GET":
        # Return a proper SSE response for connection
        response = HttpResponse(
            content_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        response.write("data: {}\n\n")
        return response

    # Handle POST requests for API actions (JSON-RPC 2.0)
    if request.method != "POST":
        return JsonResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Method not allowed"},
            "id": None
        }, status=405)

    # Special case for empty requests
    if len(request.body) == 0:
        return JsonResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error: empty request"},
            "id": None
        }, status=400)

    try:
        # Parse the request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error: invalid JSON"},
                "id": None
            }, status=400)

        # Check for required JSON-RPC 2.0 fields
        jsonrpc_version = data.get("jsonrpc")
        request_id = data.get("id")
        method = data.get("method")
        params = data.get("params", {})

        # Validate JSON-RPC 2.0 version
        if jsonrpc_version != "2.0":
            return JsonResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid Request: version must be 2.0"},
                "id": request_id
            }, status=400)

        # Authenticate the user from the token
        user = get_user_from_token(request)
        if not user:
            return JsonResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32001, "message": "Invalid or expired token"},
                "id": request_id
            }, status=401)

        # Handle different methods according to JSON-RPC 2.0
        if method == "list_tools" or method == "tools.list":
            # Return available tools in JSON-RPC 2.0 format
            return JsonResponse({
                "jsonrpc": "2.0",
                "result": {"tools": get_available_tools()},
                "id": request_id
            })

        elif method == "list_solutions" or method == "get_solutions":
            # Get user's solutions, optionally filtered
            query = params.get('query', '')
            tag = params.get('tag', '')
            limit = int(params.get('limit', 10))

            solutions = Solution.objects.filter(author=user)

            # Apply filters if provided
            if query:
                solutions = solutions.filter(title__icontains=query) | solutions.filter(content__icontains=query)

            if tag:
                solutions = solutions.filter(tags__name__icontains=tag)

            # Limit the number of results
            solutions = solutions[:limit]

            # Format the response
            response_data = [{
                'id': solution.id,
                'title': solution.title,
                'slug': solution.slug,
                'summary': solution.summary,
                'tags': [tag.name for tag in solution.tags.all()],
                'created_at': solution.created_at.isoformat(),
                'updated_at': solution.updated_at.isoformat(),
                'view_count': solution.view_count,
            } for solution in solutions]

            return JsonResponse({
                "jsonrpc": "2.0",
                "result": {'solutions': response_data},
                "id": request_id
            })

        elif method == "get_solution":
            # Get a specific solution by slug
            slug = params.get('slug')

            if not slug:
                return JsonResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "Invalid params: Solution slug is required"},
                    "id": request_id
                }, status=400)

            try:
                solution = Solution.objects.get(slug=slug, author=user)

                # Format the response
                response_data = {
                    'id': solution.id,
                    'title': solution.title,
                    'slug': solution.slug,
                    'content': solution.content,
                    'summary': solution.summary,
                    'tags': [tag.name for tag in solution.tags.all()],
                    'created_at': solution.created_at.isoformat(),
                    'updated_at': solution.updated_at.isoformat(),
                    'view_count': solution.view_count,
                }

                return JsonResponse({
                    "jsonrpc": "2.0",
                    "result": {'solution': response_data},
                    "id": request_id
                })
            except Solution.DoesNotExist:
                return JsonResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "Solution not found"},
                    "id": request_id
                }, status=404)

        elif method == "create_solution":
            # Create a new solution
            title = params.get('title')
            content = params.get('content')
            tags = params.get('tags', [])
            is_published = params.get('is_published', True)

            if not title or not content or not tags:
                return JsonResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "Invalid params: Title, content, and tags are required"},
                    "id": request_id
                }, status=400)

            if len(tags) < 5:
                return JsonResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "Invalid params: At least 5 tags are required"},
                    "id": request_id
                }, status=400)

            # Create the solution
            solution = Solution(
                title=title,
                content=content,
                author=user,
                is_published=is_published
            )
            solution.save()

            # Add tags
            tag_objects = Tag.get_or_create_tags(tags)
            solution.tags.set(tag_objects)

            # Format the response
            response_data = {
                'id': solution.id,
                'title': solution.title,
                'slug': solution.slug,
                'summary': solution.summary,
                'url': f"/solutions/{solution.slug}/"
            }

            return JsonResponse({
                "jsonrpc": "2.0",
                "result": {'solution': response_data, 'message': 'Solution created successfully'},
                "id": request_id
            })

        elif method == "update_solution":
            # Update an existing solution
            slug = params.get('slug')
            title = params.get('title')
            content = params.get('content')
            tags = params.get('tags')
            is_published = params.get('is_published')
            comment = params.get('comment', 'Updated via MCP')

            if not slug:
                return JsonResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "Invalid params: Solution slug is required"},
                    "id": request_id
                }, status=400)

            try:
                solution = Solution.objects.get(slug=slug, author=user)

                # Update fields if provided
                if title:
                    solution.title = title

                if content:
                    solution.content = content

                if is_published is not None:
                    solution.is_published = is_published

                # Save the solution
                solution.save()

                # Update tags if provided
                if tags and len(tags) >= 5:
                    tag_objects = Tag.get_or_create_tags(tags)
                    solution.tags.set(tag_objects)

                # Create a version with the comment
                from solutions.models import SolutionVersion
                SolutionVersion.objects.create(
                    solution=solution,
                    content=solution.content,
                    change_comment=comment,
                    created_by=user
                )

                # Format the response
                response_data = {
                    'id': solution.id,
                    'title': solution.title,
                    'slug': solution.slug,
                    'summary': solution.summary,
                    'url': f"/solutions/{solution.slug}/"
                }

                return JsonResponse({
                    "jsonrpc": "2.0",
                    "result": {'solution': response_data, 'message': 'Solution updated successfully'},
                    "id": request_id
                })
            except Solution.DoesNotExist:
                return JsonResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "Solution not found"},
                    "id": request_id
                }, status=404)

        else:
            return JsonResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id
            }, status=400)

    except Exception as e:
        logger.error(f"Error in MCP endpoint: {str(e)}")
        return JsonResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": "Internal error: An error occurred processing your request"},
            "id": data.get("id") if 'data' in locals() else None
        }, status=500)


def get_available_tools():
    """
    Returns the list of available tools in the format expected by MCP clients.
    """
    return [
        {
            "name": "get_solutions",
            "description": "Get a list of your solutions with optional filtering",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional search term to filter solutions"
                    },
                    "tag": {
                        "type": "string",
                        "description": "Optional tag name to filter solutions"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of solutions to return (default: 10)"
                    }
                }
            }
        },
        {
            "name": "get_solution",
            "description": "Get details of a specific solution by its slug",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "The slug of the solution to retrieve"
                    }
                },
                "required": ["slug"]
            }
        },
        {
            "name": "create_solution",
            "description": "Create a new solution in your account",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the solution"
                    },
                    "content": {
                        "type": "string",
                        "description": "Markdown content of the solution"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "At least 5 tags for the solution"
                    },
                    "is_published": {
                        "type": "boolean",
                        "description": "Whether the solution should be published (default: true)"
                    }
                },
                "required": ["title", "content", "tags"]
            }
        },
        {
            "name": "update_solution",
            "description": "Update an existing solution",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "The slug of the solution to update"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title for the solution (optional)"
                    },
                    "content": {
                        "type": "string",
                        "description": "New markdown content for the solution (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tags for the solution (at least 5 required, optional)"
                    },
                    "is_published": {
                        "type": "boolean",
                        "description": "Whether the solution should be published (optional)"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional comment describing the changes made"
                    }
                },
                "required": ["slug"]
            }
        }
    ]
