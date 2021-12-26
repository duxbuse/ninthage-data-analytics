from os import getenv
import requests
from flask.wrappers import Request
from dotenv import load_dotenv

from http400 import handle_400
from http408 import handle_408
from http_error_catch_all import handle_error
from discord_message_limits import truncate_message


def function_discord_error_reporting(request: Request):
    if request.json:
        print(f"{request.json=}")
        if not request.json.get("data") and not request.json.get("data").get("name"):
            pass  # TODO: We should raise an exception here, but we also want to submit this info back to discord

        FILE_NAME = request.json["data"]["name"]
        json_message = {
            "content": "",
            "embeds": [
                {
                    "author": {
                        "name": FILE_NAME,
                    },
                    "title": "Errors:",
                    "description": "",
                    "color": 15224675,
                    "fields": [
                        {
                            "name": "\u200B",
                            "value": "Got an issue raise it [here](https://github.com/duxbuse/ninthage-data-analytics/issues)!",
                        }
                    ],
                }
            ],
        }
        error_code: int = 418
        if request.json.get("error_code"):
            error_code = request.json.get("error_code").get("code", 418)
        elif request.json.get("error"):
            error_code = request.json.get("error").get("code", 418)

        print(f"{error_code=}")
        if error_code == 400:  # value errors
            handle_400(request, json_message)

        elif error_code == 408:  # Timeout
            handle_408(request, json_message)

        else:  # default
            handle_error(request, json_message)
        print(f"{json_message=}")

        truncate_message(json_message)
        print(f"after truncation {json_message=}")

        TOKEN = getenv("DISCORD_WEBHOOK_TOKEN")
        WEBHOOK_ID = getenv("DISCORD_WEBHOOK_ID")

        url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
        headers = {
            "Authorization": f"Bot {TOKEN}",
            "Accept": "application/json",
            "User-Agent": "ninthage-data-analytics/1.1.0",
            "Content-Type": "application/json",
        }

        r = requests.post(url, headers=headers, json=json_message)

        print(f"discord status code: {r.status_code}")
        print(f"discord text: {r.text}")
        if r.status_code != 200 or r.status_code != 204:
            return r.text, r.status_code

        return "reported to discord", 200
    return "There was no json payload", 500


if __name__ == "__main__":
    load_dotenv()
    json_message = {
        "data": {
            "bucket": "tournament-lists",
            "contentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "crc32c": "kBvh6w==",
            "etag": "CJv42KWL4fQCEAE=",
            "generation": "1639409228594203",
            "id": "tournament-lists/Cossacks Raid - Master.docx/1639409228594203",
            "kind": "storage#object",
            "md5Hash": "z1DQCBrK4l8ONRfCMgW60A==",
            "mediaLink": "https://www.googleapis.com/download/storage/v1/b/tournament-lists/o/Cossacks%20Raid%20-%20Master.docx?generation=1639409228594203&alt=media",
            "metageneration": "1",
            "name": "Cossacks Raid - Master.docx",
            "selfLink": "https://www.googleapis.com/storage/v1/b/tournament-lists/o/Cossacks%20Raid%20-%20Master.docx",
            "size": "63743",
            "storageClass": "STANDARD",
            "timeCreated": "2021-12-13T15:27:08.627Z",
            "timeStorageClassUpdated": "2021-12-13T15:27:08.627Z",
            "updated": "2021-12-13T15:27:08.627Z",
        },
        "error": {
            "body": {
                "message": [
                    "Army Block has to few lines for validation.\nRequires at minimum name, army, and 4 units.\n\nWhole army list = ['Léopold', 'Daemon Legions']",
                    "player: \"Infernal Dwarves\" not found in TK player list: ['Ed', 'Ciara', 'Speedy', 'Damian \"Milczek\" Bronowicki', 'Romek', 'Harry Axe', 'Ever', 'AKU', 'Blazej', 'Kamil Oleński', 'Adam', 'Lohost', 'Heptun', 'Azurix', 'Michał \"Futhus\" Pierzchalski', 'Kacper Mąkosa ', 'Michał', 'Daniel Reszka', 'Glonojad', 'Michas', 'rafixator', 'Turek', 'Shakin Dudi', 'X.Maciek', 'Kacper Pielaszek', 'Tocz', 'Crane', 'WarX', 'Trojek', 'Krzysztof', 'grimgorg', 'Pershing', 'Galahad', 'Rilam', \"Tomasz 'Handełek' Domagalski\", 'Maciek', 'Dajed', 'Papryk', 'Michał Kołakowski', 'Marcin Lipiński', 'Dębek', 'Arkadiusz Arecki Łysiak', 'Wulpis', 'Riplay', 'Mamut', 'pazdzioch', 'Bobson', 'Szymu', 'Glegut', 'Big Boss M.', 'Panterq', 'Arrander', 'Semi', 'Marek Golan', 'Jarekk', 'Jacek Drob', 'Fabrice Babnik', 'GreMliN', 'PSz', 'Dravenlord', 'Danrakh', 'goboss', 'Léopold', 'Nicolas', 'Piotrek', 'GarG', 'Kaare Siesing', 'Stanislaw Scheiner', 'Pierre-Hugues ', 'Michał Rusinek', 'Dziop', 'Sebastian Daszkiewicz', 'Bartłomiej', 'Terminator', 'Guldur', 'Marcin Szlasa-Rokicki', 'Wojtuś', 'Myth', 'Król Słońca Boski Solo', 'Olek ', 'Jezus', 'Hoax', 'Imrikko', 'Matis Kingdom of Equitaine', 'Cezar', 'player1', 'player2', 'player3', 'player4', 'player5']\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id=3577)",
                    "player: \"Infernal Dwarves\" not found in TK player list: ['Ed', 'Ciara', 'Speedy', 'Damian \"Milczek\" Bronowicki', 'Romek', 'Harry Axe', 'Ever', 'AKU', 'Blazej', 'Kamil Oleński', 'Adam', 'Lohost', 'Heptun', 'Azurix', 'Michał \"Futhus\" Pierzchalski', 'Kacper Mąkosa ', 'Michał', 'Daniel Reszka', 'Glonojad', 'Michas', 'rafixator', 'Turek', 'Shakin Dudi', 'X.Maciek', 'Kacper Pielaszek', 'Tocz', 'Crane', 'WarX', 'Trojek', 'Krzysztof', 'grimgorg', 'Pershing', 'Galahad', 'Rilam', \"Tomasz 'Handełek' Domagalski\", 'Maciek', 'Dajed', 'Papryk', 'Michał Kołakowski', 'Marcin Lipiński', 'Dębek', 'Arkadiusz Arecki Łysiak', 'Wulpis', 'Riplay', 'Mamut', 'pazdzioch', 'Bobson', 'Szymu', 'Glegut', 'Big Boss M.', 'Panterq', 'Arrander', 'Semi', 'Marek Golan', 'Jarekk', 'Jacek Drob', 'Fabrice Babnik', 'GreMliN', 'PSz', 'Dravenlord', 'Danrakh', 'goboss', 'Léopold', 'Nicolas', 'Piotrek', 'GarG', 'Kaare Siesing', 'Stanislaw Scheiner', 'Pierre-Hugues ', 'Michał Rusinek', 'Dziop', 'Sebastian Daszkiewicz', 'Bartłomiej', 'Terminator', 'Guldur', 'Marcin Szlasa-Rokicki', 'Wojtuś', 'Myth', 'Król Słońca Boski Solo', 'Olek ', 'Jezus', 'Hoax', 'Imrikko', 'Matis Kingdom of Equitaine', 'Cezar', 'player1', 'player2', 'player3', 'player4', 'player5']\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id=3577)",
                    "player: \"OnG\" not found in TK player list: ['Ed', 'Ciara', 'Speedy', 'Damian \"Milczek\" Bronowicki', 'Romek', 'Harry Axe', 'Ever', 'AKU', 'Blazej', 'Kamil Oleński', 'Adam', 'Lohost', 'Heptun', 'Azurix', 'Michał \"Futhus\" Pierzchalski', 'Kacper Mąkosa ', 'Michał', 'Daniel Reszka', 'Glonojad', 'Michas', 'rafixator', 'Turek', 'Shakin Dudi', 'X.Maciek', 'Kacper Pielaszek', 'Tocz', 'Crane', 'WarX', 'Trojek', 'Krzysztof', 'grimgorg', 'Pershing', 'Galahad', 'Rilam', \"Tomasz 'Handełek' Domagalski\", 'Maciek', 'Dajed', 'Papryk', 'Michał Kołakowski', 'Marcin Lipiński', 'Dębek', 'Arkadiusz Arecki Łysiak', 'Wulpis', 'Riplay', 'Mamut', 'pazdzioch', 'Bobson', 'Szymu', 'Glegut', 'Big Boss M.', 'Panterq', 'Arrander', 'Semi', 'Marek Golan', 'Jarekk', 'Jacek Drob', 'Fabrice Babnik', 'GreMliN', 'PSz', 'Dravenlord', 'Danrakh', 'goboss', 'Léopold', 'Nicolas', 'Piotrek', 'GarG', 'Kaare Siesing', 'Stanislaw Scheiner', 'Pierre-Hugues ', 'Michał Rusinek', 'Dziop', 'Sebastian Daszkiewicz', 'Bartłomiej', 'Terminator', 'Guldur', 'Marcin Szlasa-Rokicki', 'Wojtuś', 'Myth', 'Król Słońca Boski Solo', 'Olek ', 'Jezus', 'Hoax', 'Imrikko', 'Matis Kingdom of Equitaine', 'Cezar', 'player1', 'player2', 'player3', 'player4', 'player5']\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id=3577)",
                    "player: \"Dread Elves\" not found in TK player list: ['Ed', 'Ciara', 'Speedy', 'Damian \"Milczek\" Bronowicki', 'Romek', 'Harry Axe', 'Ever', 'AKU', 'Blazej', 'Kamil Oleński', 'Adam', 'Lohost', 'Heptun', 'Azurix', 'Michał \"Futhus\" Pierzchalski', 'Kacper Mąkosa ', 'Michał', 'Daniel Reszka', 'Glonojad', 'Michas', 'rafixator', 'Turek', 'Shakin Dudi', 'X.Maciek', 'Kacper Pielaszek', 'Tocz', 'Crane', 'WarX', 'Trojek', 'Krzysztof', 'grimgorg', 'Pershing', 'Galahad', 'Rilam', \"Tomasz 'Handełek' Domagalski\", 'Maciek', 'Dajed', 'Papryk', 'Michał Kołakowski', 'Marcin Lipiński', 'Dębek', 'Arkadiusz Arecki Łysiak', 'Wulpis', 'Riplay', 'Mamut', 'pazdzioch', 'Bobson', 'Szymu', 'Glegut', 'Big Boss M.', 'Panterq', 'Arrander', 'Semi', 'Marek Golan', 'Jarekk', 'Jacek Drob', 'Fabrice Babnik', 'GreMliN', 'PSz', 'Dravenlord', 'Danrakh', 'goboss', 'Léopold', 'Nicolas', 'Piotrek', 'GarG', 'Kaare Siesing', 'Stanislaw Scheiner', 'Pierre-Hugues ', 'Michał Rusinek', 'Dziop', 'Sebastian Daszkiewicz', 'Bartłomiej', 'Terminator', 'Guldur', 'Marcin Szlasa-Rokicki', 'Wojtuś', 'Myth', 'Król Słońca Boski Solo', 'Olek ', 'Jezus', 'Hoax', 'Imrikko', 'Matis Kingdom of Equitaine', 'Cezar', 'player1', 'player2', 'player3', 'player4', 'player5']\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id=3577)",
                    "player: \"Daemon Legions\" not found in TK player list: ['Ed', 'Ciara', 'Speedy', 'Damian \"Milczek\" Bronowicki', 'Romek', 'Harry Axe', 'Ever', 'AKU', 'Blazej', 'Kamil Oleński', 'Adam', 'Lohost', 'Heptun', 'Azurix', 'Michał \"Futhus\" Pierzchalski', 'Kacper Mąkosa ', 'Michał', 'Daniel Reszka', 'Glonojad', 'Michas', 'rafixator', 'Turek', 'Shakin Dudi', 'X.Maciek', 'Kacper Pielaszek', 'Tocz', 'Crane', 'WarX', 'Trojek', 'Krzysztof', 'grimgorg', 'Pershing', 'Galahad', 'Rilam', \"Tomasz 'Handełek' Domagalski\", 'Maciek', 'Dajed', 'Papryk', 'Michał Kołakowski', 'Marcin Lipiński', 'Dębek', 'Arkadiusz Arecki Łysiak', 'Wulpis', 'Riplay', 'Mamut', 'pazdzioch', 'Bobson', 'Szymu', 'Glegut', 'Big Boss M.', 'Panterq', 'Arrander', 'Semi', 'Marek Golan', 'Jarekk', 'Jacek Drob', 'Fabrice Babnik', 'GreMliN', 'PSz', 'Dravenlord', 'Danrakh', 'goboss', 'Léopold', 'Nicolas', 'Piotrek', 'GarG', 'Kaare Siesing', 'Stanislaw Scheiner', 'Pierre-Hugues ', 'Michał Rusinek', 'Dziop', 'Sebastian Daszkiewicz', 'Bartłomiej', 'Terminator', 'Guldur', 'Marcin Szlasa-Rokicki', 'Wojtuś', 'Myth', 'Król Słońca Boski Solo', 'Olek ', 'Jezus', 'Hoax', 'Imrikko', 'Matis Kingdom of Equitaine', 'Cezar', 'player1', 'player2', 'player3', 'player4', 'player5']\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id=3577)",
                    "player: \"Highborn Elves\" not found in TK player list: ['Ed', 'Ciara', 'Speedy', 'Damian \"Milczek\" Bronowicki', 'Romek', 'Harry Axe', 'Ever', 'AKU', 'Blazej', 'Kamil Oleński', 'Adam', 'Lohost', 'Heptun', 'Azurix', 'Michał \"Futhus\" Pierzchalski', 'Kacper Mąkosa ', 'Michał', 'Daniel Reszka', 'Glonojad', 'Michas', 'rafixator', 'Turek', 'Shakin Dudi', 'X.Maciek', 'Kacper Pielaszek', 'Tocz', 'Crane', 'WarX', 'Trojek', 'Krzysztof', 'grimgorg', 'Pershing', 'Galahad', 'Rilam', \"Tomasz 'Handełek' Domagalski\", 'Maciek', 'Dajed', 'Papryk', 'Michał Kołakowski', 'Marcin Lipiński', 'Dębek', 'Arkadiusz Arecki Łysiak', 'Wulpis', 'Riplay', 'Mamut', 'pazdzioch', 'Bobson', 'Szymu', 'Glegut', 'Big Boss M.', 'Panterq', 'Arrander', 'Semi', 'Marek Golan', 'Jarekk', 'Jacek Drob', 'Fabrice Babnik', 'GreMliN', 'PSz', 'Dravenlord', 'Danrakh', 'goboss', 'Léopold', 'Nicolas', 'Piotrek', 'GarG', 'Kaare Siesing', 'Stanislaw Scheiner', 'Pierre-Hugues ', 'Michał Rusinek', 'Dziop', 'Sebastian Daszkiewicz', 'Bartłomiej', 'Terminator', 'Guldur', 'Marcin Szlasa-Rokicki', 'Wojtuś', 'Myth', 'Król Słońca Boski Solo', 'Olek ', 'Jezus', 'Hoax', 'Imrikko', 'Matis Kingdom of Equitaine', 'Cezar', 'player1', 'player2', 'player3', 'player4', 'player5']\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id=3577)",
                    "player: \"Warriors of the Dark Gods\" not found in TK player list: ['Ed', 'Ciara', 'Speedy', 'Damian \"Milczek\" Bronowicki', 'Romek', 'Harry Axe', 'Ever', 'AKU', 'Blazej', 'Kamil Oleński', 'Adam', 'Lohost', 'Heptun', 'Azurix', 'Michał \"Futhus\" Pierzchalski', 'Kacper Mąkosa ', 'Michał', 'Daniel Reszka', 'Glonojad', 'Michas', 'rafixator', 'Turek', 'Shakin Dudi', 'X.Maciek', 'Kacper Pielaszek', 'Tocz', 'Crane', 'WarX', 'Trojek', 'Krzysztof', 'grimgorg', 'Pershing', 'Galahad', 'Rilam', \"Tomasz 'Handełek' Domagalski\", 'Maciek', 'Dajed', 'Papryk', 'Michał Kołakowski', 'Marcin Lipiński', 'Dębek', 'Arkadiusz Arecki Łysiak', 'Wulpis', 'Riplay', 'Mamut', 'pazdzioch', 'Bobson', 'Szymu', 'Glegut', 'Big Boss M.', 'Panterq', 'Arrander', 'Semi', 'Marek Golan', 'Jarekk', 'Jacek Drob', 'Fabrice Babnik', 'GreMliN', 'PSz', 'Dravenlord', 'Danrakh', 'goboss', 'Léopold', 'Nicolas', 'Piotrek', 'GarG', 'Kaare Siesing', 'Stanislaw Scheiner', 'Pierre-Hugues ', 'Michał Rusinek', 'Dziop', 'Sebastian Daszkiewicz', 'Bartłomiej', 'Terminator', 'Guldur', 'Marcin Szlasa-Rokicki', 'Wojtuś', 'Myth', 'Król Słońca Boski Solo', 'Olek ', 'Jezus', 'Hoax', 'Imrikko', 'Matis Kingdom of Equitaine', 'Cezar', 'player1', 'player2', 'player3', 'player4', 'player5']\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id=3577)",
                    "player: \"VS\" not found in TK player list: ['Ed', 'Ciara', 'Speedy', 'Damian \"Milczek\" Bronowicki', 'Romek', 'Harry Axe', 'Ever', 'AKU', 'Blazej', 'Kamil Oleński', 'Adam', 'Lohost', 'Heptun', 'Azurix', 'Michał \"Futhus\" Pierzchalski', 'Kacper Mąkosa ', 'Michał', 'Daniel Reszka', 'Glonojad', 'Michas', 'rafixator', 'Turek', 'Shakin Dudi', 'X.Maciek', 'Kacper Pielaszek', 'Tocz', 'Crane', 'WarX', 'Trojek', 'Krzysztof', 'grimgorg', 'Pershing', 'Galahad', 'Rilam', \"Tomasz 'Handełek' Domagalski\", 'Maciek', 'Dajed', 'Papryk', 'Michał Kołakowski', 'Marcin Lipiński', 'Dębek', 'Arkadiusz Arecki Łysiak', 'Wulpis', 'Riplay', 'Mamut', 'pazdzioch', 'Bobson', 'Szymu', 'Glegut', 'Big Boss M.', 'Panterq', 'Arrander', 'Semi', 'Marek Golan', 'Jarekk', 'Jacek Drob', 'Fabrice Babnik', 'GreMliN', 'PSz', 'Dravenlord', 'Danrakh', 'goboss', 'Léopold', 'Nicolas', 'Piotrek', 'GarG', 'Kaare Siesing', 'Stanislaw Scheiner', 'Pierre-Hugues ', 'Michał Rusinek', 'Dziop', 'Sebastian Daszkiewicz', 'Bartłomiej', 'Terminator', 'Guldur', 'Marcin Szlasa-Rokicki', 'Wojtuś', 'Myth', 'Król Słońca Boski Solo', 'Olek ', 'Jezus', 'Hoax', 'Imrikko', 'Matis Kingdom of Equitaine', 'Cezar', 'player1', 'player2', 'player3', 'player4', 'player5']\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id=3577)",
                    "\n Number of lists read: 70 did not equal number of players on tourneykeeper: 90\n Players read from file: ['Fabrice Babnik', 'Kaare Siesing', 'Nicolas', 'Pierre-Hugues', 'Ciara', \"Damian 'Milczek' Bronowicki\", 'Ever', 'Speedy', 'Romek', 'Kamil Oleński', 'Rilam', 'Adam', 'Crane', 'Lohost', 'Michas', 'Michał', 'Imrikko', 'Daniel Reszka', 'Riplay', 'Michał Kołakowski', 'Tocz', 'Undying Dynasties', 'X Maciek', 'Jacek Drob', 'Turek', 'Jarekk', 'Big Boss M.', 'Guldur', 'Panterq', 'Rafixator', 'Kacper Pielasze', 'Dziop', 'Goboss', 'Grimgorg', 'Olek', 'WarX', 'Pershing', 'Trojek', 'Michał Rusinek', 'Jezus', 'Marek Golan', 'Maciek', 'Arkadiusz Arecki Łysiak', 'Papryk', 'Matis Kingdom of Equitaine', 'Pazdzioch', 'Glegut', 'Bobson', 'Blazej', 'Terminator', 'Król Słońca Boski Solo', 'Bartłomiej', 'Myth', 'Cezar', 'Dravenlord', 'Szymu', 'Mamut', 'Danrakh', 'Piotrek', 'PSZ', 'GARG', 'Gremlin', 'SE', 'Galahad', 'Wulpis', 'Glonojad', 'Harry Axe', 'AKU', 'Ed', 'Hoax']\n Players read from TK: dict_keys(['Ed', 'Ciara', 'Speedy', 'Damian \"Milczek\" Bronowicki', 'Romek', 'Harry Axe', 'Ever', 'AKU', 'Blazej', 'Kamil Oleński', 'Adam', 'Lohost', 'Heptun', 'Azurix', 'Michał \"Futhus\" Pierzchalski', 'Kacper Mąkosa ', 'Michał', 'Daniel Reszka', 'Glonojad', 'Michas', 'rafixator', 'Turek', 'Shakin Dudi', 'X.Maciek', 'Kacper Pielaszek', 'Tocz', 'Crane', 'WarX', 'Trojek', 'Krzysztof', 'grimgorg', 'Pershing', 'Galahad', 'Rilam', \"Tomasz 'Handełek' Domagalski\", 'Maciek', 'Dajed', 'Papryk', 'Michał Kołakowski', 'Marcin Lipiński', 'Dębek', 'Arkadiusz Arecki Łysiak', 'Wulpis', 'Riplay', 'Mamut', 'pazdzioch', 'Bobson', 'Szymu', 'Glegut', 'Big Boss M.', 'Panterq', 'Arrander', 'Semi', 'Marek Golan', 'Jarekk', 'Jacek Drob', 'Fabrice Babnik', 'GreMliN', 'PSz', 'Dravenlord', 'Danrakh', 'goboss', 'Léopold', 'Nicolas', 'Piotrek', 'GarG', 'Kaare Siesing', 'Stanislaw Scheiner', 'Pierre-Hugues ', 'Michał Rusinek', 'Dziop', 'Sebastian Daszkiewicz', 'Bartłomiej', 'Terminator', 'Guldur', 'Marcin Szlasa-Rokicki', 'Wojtuś', 'Myth', 'Król Słońca Boski Solo', 'Olek ', 'Jezus', 'Hoax', 'Imrikko', 'Matis Kingdom of Equitaine', 'Cezar', 'player1', 'player2', 'player3', 'player4', 'player5'])\n ",
                ]
            },
            "code": 400,
            "headers": {
                "Alt-Svc": 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000,h3-Q050=":443"; ma=2592000,h3-Q046=":443"; ma=2592000,h3-Q043=":443"; ma=2592000,quic=":443"; ma=2592000; v="46,43"',
                "Cache-Control": "private",
                "Content-Length": "36",
                "Content-Type": "text/plain; charset=utf-8",
                "Date": "Mon, 13 Dec 2021 15:29:09 GMT",
                "Server": "Google Frontend",
                "X-Cloud-Trace-Context": "2e5ad196cccd48bce38f390afb9b2e41;o=1",
                "X-Content-Type-Options": "nosniff",
            },
            "message": "HTTP server responded with error code 408",
            "tags": ["HttpError"],
        },
    }
    request_obj = Request.from_values(json=json_message)
    function_discord_error_reporting(request_obj)
