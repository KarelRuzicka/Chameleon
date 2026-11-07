# Chameleon
***Show your true colors!*** A Discord bot that lets users self-assign custom name colors.

## Features
- Users can set their own name color from hex codes
- Users can reset their name color to default
- User color is removed when they leave the server

## Commands
- `/namecolor <hex>` - Set your name color to the specified hex code (e.g., `/namecolor #FF0000`)
- `/removenamecolor` - Reset your name color to default

## Important Notes
- The added color roles will be added **below** the bot's highest role. Make sure the bot's role is high enough to manage color roles.
- Each added color role is named `Color`. Make sure there are no other roles with the same name to avoid conflicts.

## Permission Requirements
- `Manage Roles` - Required to create and delete color roles for users.
- `Send Messages` - Required to respond to user commands.
