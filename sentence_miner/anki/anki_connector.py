import requests

class AnkiConnector:
    def __init__(self, url="http://localhost:8765"):
        self.url = url

    def add_note_to_deck(self, deck_name, front_text, back_text, audio=None):
        note = {
            "deckName": deck_name,
            "modelName": "Basic",
            "fields": {
                "Front": front_text,
                "Back": back_text
            },
            "tags": []
        }

        if audio:
            note['audio'] = [{
                "path": audio['path'],
                "filename": audio['filename'],
                "fields": [audio['fields']]
            }]

        payload = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": note
            }
        }

        try:
            response = requests.post(self.url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if 'error' in result and result['error'] is None:
                    return True, f"Note successfully added to deck {deck_name}"
                else:
                    return False, f"Failed to add card: {result['error']}"
            else:
                return False, "Failed to connect to AnkiConnect."
        except requests.exceptions.RequestException as e:
            return False, f"Failed to connect to AnkiConnect: {e}"

    def get_decks(self):
        payload = {
            "action": "deckNamesAndIds",
            "version": 6
        }
        try:
            response = requests.post(self.url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if 'error' in result and result['error'] is None:
                    return list(result['result'].keys())
                else:
                    print("Error fetching decks:", result['error'])
            else:
                print("Failed to connect to AnkiConnect.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to AnkiConnect: {e}")
        return {}

    def get_deck_card_count(self, deck_name):
        payload = {
            "action": "findCards",
            "version": 6,
            "params": {
                "query": f"deck:{deck_name}"
            }
        }
        try:
            response = requests.post(self.url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if 'error' in result and result['error'] is None:
                    return len(result['result'])
                else:
                    print(f"Error fetching card count for deck {deck_name}:", result['error'])
            else:
                print(f"Failed to connect to AnkiConnect for deck {deck_name}.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to AnkiConnect: {e}")
        return 0