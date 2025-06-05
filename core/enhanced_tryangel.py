import os
import time
import json
import datetime
from gtts import gTTS
from playsound import playsound
from insf_local_learnerSOL_ready_defaulted import INSFLocalLearner

class EnhancedTryAngel:
    def __init__(self, user_id='utilisateur_defaut_001'):
        self.user_id = user_id
        self.learner = INSFLocalLearner()
        self.profile = self.learner.create_or_load_user_profile(user_id)
        self.voice_dir = 'voices'
        self.memory_file = 'tryangel_memory_log.json'
        os.makedirs(self.voice_dir, exist_ok=True)
        self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                self.memory = json.load(f)
        else:
            self.memory = []

    def save_memory(self, message, response):
        entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'message': message,
            'response': response
        }
        self.memory.append(entry)
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2)

    def speak(self, text):
        print(f'TryAngel: {text}')
        filename = os.path.join(self.voice_dir, f"response_{int(time.time())}.mp3")
        tts = gTTS(text=text, lang='fr')
        tts.save(filename)
        try:
            playsound(filename)
        except Exception as e:
            print(f'[Erreur audio] {e}')
        os.remove(filename)
        self.learner.record_voice_context(self.user_id, self.profile['last_emotion'], self.profile['preferred_voice'], 'positif')

    def ask_feedback(self):
        feedback = input('Ton avis (positif/confus/négatif) : ').strip().lower()
        emotion = input('Ton émotion actuelle (joyeux/triste/stressé/etc.) : ').strip().lower()
        self.learner.record_interaction(self.user_id, self.profile['preferred_voice'], feedback, emotion)
        return feedback

    def run(self):
        self.speak('Bonjour, je suis TryAngel enrichie. Pose-moi ta question.')
        while True:
            user_input = input('Toi: ')
            if user_input.lower() in ['exit', 'quit']:
                self.speak('À bientôt.')
                break
            if not user_input.strip():
                self.speak('Je n’ai rien compris. Répète, s’il te plaît.')
                continue
            response = f"Je reçois : {user_input[:80]}. Je le retiens pour m’en souvenir."
            self.save_memory(user_input, response)
            self.speak(response)
            self.ask_feedback()

if __name__ == '__main__':
    EnhancedTryAngel().run()