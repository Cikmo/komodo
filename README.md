# Pathfinder for new Komodo

A Politics and War discord bot.

## Extrenal Requirements

- Poetry
- Postgres

## Basic Setup

1. Clone the repository

2. cd into the directory, and install the dependencies

```bash
poetry install
```

3. Run the program to generate the setting file

```bash
./komodo run [dev|prod]
```

4. Make sure you have a postgres database running and create a database for the bot.

5. Fill in the settings file. The settings file is located at `./settings.toml` for production and `./settings.dev.toml` for development.

6. Run migrations. This will create the tables in the database.

```bash
piccolo migrations forwards komodo
```

7. Finally, run the bot

```bash
./komodo run [dev|prod]
```

## Advanced Setup

Settings can be set either through the settings file or through environment variables. To let the program know that you want to use environment variables, set the `KOMODO_USE_FILE` environment variable to `false`. This will also prevent the program from generating a settings file.

The format for the environment variables is `KOMODO_<SECTION>_<KEY>`. For example, to set the `token` key in the `discord` section, you would set the `KOMODO_DISCORD_TOKEN` environment variable.

There is a handy script that will generate the environment variables for you based on the toml settings. To use it, run

```bash
./komodo run generate_env <path to settings file> [-o <output file>]
```

If you don't specify an output file, the script will print the environment variables to the console.

## Running in Production

It is recommended to run the bot in "prod" mode when running it in a production environment. This is done simply by running `./komodo run prod`. This will make the bot run in a more optimized way.

Please, for the love of god, use environment variables to set the settings in a production environment. This is much more secure than using a settings file, and sooo much easier to manage if you're using something like Docker.

## TODO:

- Add an argument to the run command to use environment variables instead of the settings file
- Add an argument to the run command to run migrations

To create pydantic models from graphql schema:

```bash
datamodel-codegen --input schema.graphql --input-file-type graphql --output model.py
```

or

```bash
ariadne_codegen
```

### Progress on fixing nullable types in the api schema:

- [x] ApiKeyDetails
- [x] ApiKeyPermissions
- [x] Nation
- [x] City
- [x] Treasure
- [x] Alliance
- [x] AlliancePosition
- [x] War
- [x] WarAttack
- [x] GameInfo
- [x] Radiation
- [x] TopTradeInfo
- [x] TopTradeResourceInfo
- [x] Trade
- [x] NationResourceStat
- [x] Tradeprice
- [x] Bounty
- [x] Treaty
- [x] Bankrec
- [x] TaxBracket
- [x] TreasureTrade
- [x] Embargo
- [x] ResourceStat
- [x] ActivityStat
- [x] BannedNation
- [x] Bulletin
- [x] BulletinReply
- [x] CityInfraDamage
- [x] Award
- [x] BBTeam
- [x] BBGame
- [x] BBPlayer
- [x] Color
- [ ] ... and so on
