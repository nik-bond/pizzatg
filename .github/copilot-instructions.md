---
description: AI rules derived by SpecStory from the project AI interaction history
globs: *
---

## PROJECT OVERVIEW

This file defines all project rules, coding standards, workflow guidelines, references, documentation structures, and best practices for the AI coding assistant.

## CODE STYLE

[Existing content about code style will go here]

## FOLDER ORGANIZATION

[Existing content about folder organization will go here]

## TECH STACK

- When adding new libraries, ensure they are added to `requirements.txt`.
- After installing new libraries, run `pip install -r requirements.txt`.
- Include version numbers for libraries in `requirements.txt`.
- Add `python-dotenv>=1.0.0` to `requirements.txt` if it's not already present.

## PROJECT-SPECIFIC STANDARDS

[Existing content about project-specific standards will go here]

## WORKFLOW & RELEASE RULES

- Make regular commits to GitHub.
- Ensure there's a detailed description of changes in the commit.
- **Always make sure there's a detailed description of changes in the commit.**
- When creating a pull request, ensure it has a clear title and description.

## REFERENCE EXAMPLES

[Existing content about reference examples will go here]

## PROJECT DOCUMENTATION & CONTEXT SYSTEM

- Update `CLAUDE.md` with development logs, key findings, and test counts.

## DEBUGGING

- When tests fail, examine the test output closely to understand the root cause.
- Use print statements or a debugger to inspect variables and control flow.
- Ensure test expectations match the actual behavior of the code.
- Make sure to run `git status` to see the current status.

## FINAL DOs AND DON'Ts

- Always remember to make regular commits of any changes to the github.
- Always ensure there's a detailed description of changes in the commit.
- **Always remember to make regular commits of any changes to GitHub.**
- Don't include secrets or API keys directly in the code. Use environment variables and store them securely.
- Do not commit `.env` files to the repository. Ensure `.env` is in `.gitignore`.
- Store the bot token securely in a `.env` file and ensure `.env` is in `.gitignore`.