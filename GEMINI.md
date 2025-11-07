# How to Create a Commit Message

A good commit message should be clear, concise, and provide context for the changes being made. It should have a subject line and an optional body.

## Subject Line

The subject line should be a short, descriptive summary of the change, 50 characters or less. It should be written in the imperative mood (e.g., "Fix bug" not "Fixed bug" or "Fixes bug").

## Body

The body of the commit message is optional, but it's highly recommended for anything but the most trivial changes. It should provide more context about the change, explaining the "what" and "why" of the change, not the "how". If the change is minor and the subject line is self-explanatory, the body can be omitted.

The body should be separated from the subject line by a blank line. Each line of the body should be wrapped at 72 characters.

## Example

Here is an example of a good commit message, based on the last commit in this project:

```
feat: Initialize project with pyproject.toml and update project structure

This commit initializes the project with a pyproject.toml file, replacing the old setup.py. 

Key changes include:
- Creation of pyproject.toml for modern Python packaging.
- Cleanup of .gitignore to correctly track project files.
- Creation of a LICENSE file (MIT License).
- Explicit package discovery configuration in pyproject.toml to resolve installation issues.
- Verification of package installation and command-line entry point.
- Successful execution of all project tests.
```

### Why this is a good commit message:

*   **Subject Line:** The subject line is concise and uses the imperative mood ("Initialize"). It also uses a conventional commit prefix ("feat:") to indicate that it's a new feature.
*   **Body:** The body provides a clear and detailed explanation of the changes. It explains *why* the change was made (to modernize the packaging with `pyproject.toml`) and *what* was changed (a list of key changes).
*   **Formatting:** The body is separated from the subject by a blank line, and the list of changes makes it easy to read and understand.

## Creating Commit Messages with a Temporary File

For complex or multi-line commit messages, it is recommended to use a temporary file to ensure proper formatting.

**Steps:**
1.  Create a temporary file (e.g., `commit_message.txt`) in the project's root directory.
2.  Write your desired commit message into this file, ensuring correct line breaks and indentation.
3.  Use `git commit -F <path_to_temp_file>` to commit the changes, where `<path_to_temp_file>` is the absolute path to your temporary file.
4.  After the commit, remove the temporary file.

**Example:**

```bash
# Create the temporary commit message file
echo "feat: Implement new feature\n\nThis commit introduces a new feature to the project.\n\nKey changes include:\n- Added new functionality.\n- Updated relevant files." > commit_message.txt

# Commit the changes using the temporary file
git commit -F commit_message.txt

# Remove the temporary file
rm commit_message.txt
```