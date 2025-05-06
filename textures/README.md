# CrossyRoads Textures

This folder contains texture files for the CrossyRoads game. You can customize the game's appearance by adding or modifying texture files in the appropriate folders.

## Folder Structure

- `player/`: Contains textures for the player character (player.png)
- `grass/`: Contains textures for the grass/safe zones (grass.png)
- `road/`: Contains textures for the road (road.png)
- `cars/`: Contains textures for the cars (multiple textures allowed)

## Adding Your Own Textures

To add your own textures:

1. Place the image files in the appropriate folders
2. Make sure the file names match what the game expects:
   - Player: `player.png`
   - Grass: `grass.png`
   - Road: `road.png`
   - Cars: You can add multiple car textures with any name ending in .png or .jpg

## Texture Guidelines

- **Player**: Recommended size is about 32x32 pixels, with a transparent background (PNG format)
- **Grass**: Should be tileable and at least 40x40 pixels (the game will tile it)
- **Road**: Should be tileable and at least 40x40 pixels
- **Cars**: Various sizes are acceptable; the game will scale them to fit

## Disabling Textures

If you prefer the original simple graphics, you can disable textures by setting `USE_TEXTURES = False` in the game code, or simply remove all texture files. 