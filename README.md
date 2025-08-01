# Solutionist

A modern, collaborative, developer-focused solution-sharing platform inspired by StackOverflow but with a gist-like
solutions repository.

## Project Vision

Solutionist aims to create a community where developers can share, discover, and collaborate on high-quality solutions
to common programming problems. Unlike traditional Q&A platforms, Solutionist focuses on curated, well-documented
solutions that can be easily referenced, forked, and improved upon.

## Features

Solutionist offers a rich set of features designed to enhance collaboration and knowledge sharing:

### Solutions Management

- **Solutions List**: Browse all available solutions with filtering options.
  ![Solutions List](/static/images/SolutionsListFeature.png)

- **Solution Detail**: View comprehensive solutions with code, explanations, and metadata.
  ![Solution Detail](/static/images/SolutionDetailFeature.png)

- **Solution Creation & Editing**: Create and edit solutions with a user-friendly interface.
  ![Create or Edit Solution](/static/images/SolutionCreateOrEditFeature.png)

### Rich Content Support

- **Markdown & Mermaid Diagrams**: Write content with Markdown formatting and create diagrams using Mermaid.
  ![Markdown and Mermaid Support](/static/images/MarkdownAndMermaidFeature.png)

### Version Control

- **Version History**: Track changes to solutions over time.
  ![Version History](/static/images/VersionHistoryFeature.png)

- **Version Comparison**: Compare different versions of a solution to see what's changed.
  ![Version Comparison](/static/images/VersionComparisonFeature.png)

### User Profiles

- **User Detail**: View detailed user profiles with their contributions.
  ![User Detail](/static/images/UserDetailFeature.png)

- **User Profile Management**: Manage your profile information and settings.
  ![User Profile](/static/images/UserProfileFeature.png)

### Organization & Discovery

- **Tagging System**: Organize and discover solutions using tags.
  ![Tags Feature](/static/images/TagsFeature.png)

- **Search Functionality**: Find solutions quickly with powerful search capabilities.
  ![Search Feature](/static/images/SearchFeature.png)

### Communication

- **Comments Section**: Discuss solutions with other users through comments.

- **Notifications**: Stay updated with an integrated notification system.
  ![Notification Bell](/static/images/NotificationBellFeature.png)
  ![Notification List](/static/images/NotificationListFeature.png)

## Technology Stack

- **Backend**: Django (Python)
- **Frontend**: Django Templates with JavaScript enhancements
- **Database**: SQLite (development), PostgreSQL (production)
- **Styling**: Custom CSS with responsive design

## Setup Instructions

### Prerequisites

- Python 3.9+
- Poetry (dependency management)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/solutionist.git
   cd solutionist
   ```

2. Install dependencies using Poetry:
   ```
   poetry install
   ```

3. Activate the virtual environment:
   ```
   poetry shell
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Start the development server:
   ```
   python manage.py runserver
   ```

## Development

### Code Quality Tools

This project uses the following tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **pytest**: Testing
- **pre-commit**: Git hooks for code quality checks

### Running Tests

```
pytest
```

## Contributing

Contribution guidelines will be added soon.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
